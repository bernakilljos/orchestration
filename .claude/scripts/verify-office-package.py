#!/usr/bin/env python3
"""verify-office-package — PPTX·XLSX·HWPX 파일 단위 검증 (R347#1 · 읽기 전용).

"파일이 열린다" 와 "정상" 은 다르다 — 패키지 구조·관계·형식별 결함을 이유와 함께 보고한다.
  공통   : zip·CRC · XML 파트 문법 · (OOXML) [Content_Types].xml · 관계(.rels) 대상 파트 존재 (ECMA-376 Part 2 OPC)
  pptx   : 슬라이드 밖으로 나간 도형(크기 2% 초과 실패 · 이하 경고) · 10pt 미만 글자(경고)
  xlsx   : 수식 결과 캐시 없음(경고 · 한 번도 계산 안 된 파일) · 캐시된 오류 값 #REF!·#DIV/0! 등(실패) · 없는 시트 참조(실패)
  hwpx   : mimetype = application/hwp+zip (다르면 실패 · 없으면 경고) · Contents/header.xml · Contents/section*.xml ·
           Contents/content.hpf (manifest·spine) · 문단 수 — 공식 KS X 6101 본문 미확인, 오픈소스 파서 구현 기준
  미검증 : 실제 프로그램 렌더(PowerPoint·Excel·한컴)·내용 사실 정확성은 이 도구가 판정하지 않음 (unverified 로 표시)

usage: python verify-office-package.py <파일> [<파일> ...]   → stdout JSON 목록 · 하나라도 실패면 종료 1
"""
import json
import posixpath
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

ERR_VALUES = ("#REF!", "#DIV/0!", "#NAME?", "#VALUE!", "#N/A", "#NUM!", "#NULL!")
MIN_PT = 10
OVER_FAIL = 0.02


def _ooxml_common(z, names, fails):
    if "[Content_Types].xml" not in names:
        fails.append("[Content_Types].xml 없음 (OPC 필수 파트)")
    for n in names:
        if not n.endswith(".rels"):
            continue
        base = posixpath.dirname(posixpath.dirname(n))          # a/_rels/b.xml.rels → a
        try:
            root = ET.fromstring(z.read(n))
        except ET.ParseError:
            continue                                              # 문법 오류는 공통 검사에서 이미 보고
        for rel in root:
            if rel.get("TargetMode") == "External":
                continue
            t = rel.get("Target") or ""
            p = t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join(base, t))
            if p not in names:
                fails.append(f"관계 대상 없음: {n} → {t}")


def _pptx(path, fails, warns, stats):
    from pptx import Presentation
    prs = Presentation(path)
    W, H = prs.slide_width, prs.slide_height
    stats["slides"] = len(prs.slides)
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.left is None or sh.width is None:
                continue
            over = max(-sh.left / W, -sh.top / H, (sh.left + sh.width - W) / W, (sh.top + sh.height - H) / H)
            if over > OVER_FAIL:        # 슬라이드 크기의 2% 초과 = 내용이 잘림
                fails.append(f"슬라이드 {i}: 슬라이드 밖으로 나간 도형 «{sh.name}» ({over:.1%})")
            elif over > 0:              # 살짝 넘침 = 상자만 넘고 글은 보일 수 있음 (실물 docs/AI_Evolution_Bible_2035.pptx 0.5%)
                warns.append(f"슬라이드 {i}: 슬라이드 경계를 살짝 넘은 도형 «{sh.name}» ({over:.1%})")
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size is not None and r.font.size.pt < MIN_PT and r.text.strip():
                            warns.append(f"슬라이드 {i}: 글자 크기 {r.font.size.pt:g}pt < {MIN_PT}pt «{r.text[:20]}»")


def _xlsx(path, fails, warns, stats):
    import openpyxl
    wf = openpyxl.load_workbook(path, data_only=False)
    wv = openpyxl.load_workbook(path, data_only=True)
    sheets = set(wf.sheetnames)
    stats["sheets"], stats["formulas"] = len(sheets), 0
    ref = re.compile(r"(?:'([^']+)'|([A-Za-z_][\w.]*))!")
    for ws in wf.worksheets:
        wsv = wv[ws.title]
        for row in ws.iter_rows():
            for c in row:
                v = wsv[c.coordinate].value
                if isinstance(v, str) and v in ERR_VALUES:
                    fails.append(f"오류 값 {v}: {ws.title}!{c.coordinate}")
                if not (isinstance(c.value, str) and c.value.startswith("=")):
                    continue
                stats["formulas"] += 1
                for a, b in ref.findall(c.value):
                    name = a or b
                    if name not in sheets:
                        fails.append(f"없는 시트 참조 «{name}»: {ws.title}!{c.coordinate} {c.value}")
                if v is None:
                    warns.append(f"수식 결과 캐시 없음 (Excel 에서 열어 재계산 전에는 값이 비어 보임): {ws.title}!{c.coordinate}")


def _hwpx(z, names, fails, warns, stats, unverified):
    if "mimetype" not in names:
        warns.append("mimetype 없음 (일부 실제 파일에도 없음 · 판독기에 따라 거부 가능)")
    else:
        mt = z.read("mimetype").decode("utf-8", "replace").strip()
        if mt != "application/hwp+zip":
            fails.append(f"mimetype 값 «{mt}» ≠ application/hwp+zip")
    if "Contents/header.xml" not in names:
        fails.append("Contents/header.xml 없음 (글꼴·문단 모양)")
    secs = sorted(n for n in names if re.fullmatch(r"Contents/section\d+\.xml", n))
    if not secs:
        fails.append("Contents/section*.xml 없음 (본문)")
    if "Contents/content.hpf" not in names:
        fails.append("Contents/content.hpf 없음 (manifest·spine — 구역 순서)")
    else:
        try:
            hpf = ET.fromstring(z.read("Contents/content.hpf"))
            hrefs = {e.get("href") for e in hpf.iter() if e.tag.endswith("item")}
            for s in secs:
                if s not in hrefs:
                    warns.append(f"content.hpf manifest 에 없는 구역: {s}")
            for h in hrefs:
                if h and h.startswith("Contents/") and h not in names:
                    fails.append(f"content.hpf 가 가리키는 파트 없음: {h}")
        except ET.ParseError:
            pass
    n = 0
    for s in secs:
        try:
            n += sum(1 for e in ET.fromstring(z.read(s)).iter() if e.tag.endswith("}p") or e.tag == "p")
        except ET.ParseError:
            pass
    stats["sections"], stats["paragraphs"] = len(secs), n
    unverified.append("한컴오피스 실렌더·조판(쪽 나눔·표·그림 배치) — 이 도구로 확인 불가")


def verify(path: str) -> dict:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    fails, warns, unverified, stats = [], [], [], {}
    res = {"file": path, "format": ext, "ok": False, "fails": fails, "warns": warns, "unverified": unverified, "stats": stats}
    if ext not in ("pptx", "xlsx", "hwpx"):
        fails.append(f"지원하지 않는 형식: .{ext} (pptx·xlsx·hwpx)")
        return res
    try:
        z = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as e:
        fails.append(f"zip 패키지 아님/열기 실패: {e}")
        return res
    with z:
        bad = z.testzip()
        if bad:
            fails.append(f"zip CRC 오류: {bad}")
        names = set(z.namelist())
        for n in sorted(names):
            if n.endswith((".xml", ".rels", ".hpf")):
                try:
                    ET.fromstring(z.read(n))
                except ET.ParseError as e:
                    fails.append(f"XML 문법 오류: {n} ({e})")
        if ext == "hwpx":
            _hwpx(z, names, fails, warns, stats, unverified)
        else:
            _ooxml_common(z, names, fails)
    if ext != "hwpx" and not fails:
        try:
            (_pptx if ext == "pptx" else _xlsx)(path, fails, warns, stats)
        except Exception as e:  # 형식 라이브러리가 못 여는 파일 = 실패 (원문 기록)
            fails.append(f"{ext} 열기 실패: {type(e).__name__}: {e}")
        unverified.append(("PowerPoint" if ext == "pptx" else "Excel") + " 실렌더·재계산 결과 — 이 도구로 확인 불가")
    res["ok"] = not fails
    return res


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    out = [verify(p) for p in argv[1:]]
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if all(r["ok"] for r in out) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
