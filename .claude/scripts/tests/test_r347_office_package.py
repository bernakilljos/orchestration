"""R347#1 형식별 파일 검증기 (PPTX·XLSX·HWPX) — 서로 다른 주제의 대표 샘플 2개씩은 통과하고,
결함을 하나씩 넣은 변형은 이유와 함께 실패해야 한다 (파일이 열린다 ≠ 정상).
근거: ECMA-376 Part 2 OPC ([Content_Types].xml · 관계 대상 파트 존재) · HWPX 는 공식 규격 본문 미확인 —
오픈소스 파서 구현(mimetype = application/hwp+zip · content.hpf manifest/spine · Contents/section*.xml) 기준이라 실렌더는 미검증으로 보고."""
import importlib.util
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude" / "scripts" / "verify-office-package.py"
spec = importlib.util.spec_from_file_location("vop", SCRIPT)
vop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vop)
pptx = pytest.importorskip("pptx")
openpyxl = pytest.importorskip("openpyxl")
from pptx.util import Inches, Pt  # noqa: E402


def _rewrite(src, dst, edit):
    """zip 의 파트를 바꿔 새 파일 (edit: {이름: bytes|None(삭제)})."""
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            if it.filename in edit:
                if edit[it.filename] is not None:
                    zo.writestr(it, edit[it.filename])
                continue
            zo.writestr(it, zi.read(it.filename))
        for k, v in edit.items():
            if v is not None and k not in zi.namelist():
                zo.writestr(k, v)


# ── PPTX ─────────────────────────────────────────────────────────────────
def _pptx(path, title, bullets, extra=None):
    p = pptx.Presentation()
    s = p.slides.add_slide(p.slide_layouts[1])
    s.shapes.title.text = title
    s.placeholders[1].text = "\n".join(bullets)
    if extra:
        extra(p, s)
    p.save(str(path))
    return path


def test_pptx_samples_pass_and_defects_fail(tmp_path):
    a = _pptx(tmp_path / "a.pptx", "주문 처리 흐름", ["접수", "검증", "출고"])
    b = _pptx(tmp_path / "b.pptx", "야간 배치 일정", ["02:00 적재", "03:30 집계"])
    for f in (a, b):
        r = vop.verify(str(f))
        assert r["ok"] and r["format"] == "pptx" and not r["fails"], r

    def off(p, s):                                         # 슬라이드 밖으로 나간 도형
        t = s.shapes.add_textbox(p.slide_width - Inches(0.5), Inches(1), Inches(3), Inches(1))
        t.text_frame.text = "잘린 글"
    r = vop.verify(str(_pptx(tmp_path / "off.pptx", "x", ["y"], off)))
    assert not r["ok"] and any("슬라이드 밖" in m for m in r["fails"]), r

    def edge(p, s):                                        # 0.05in 넘침 = 경고만
        t = s.shapes.add_textbox(p.slide_width - Inches(2.95), Inches(5), Inches(3), Inches(0.5))
        t.text_frame.text = "가장자리"
    r = vop.verify(str(_pptx(tmp_path / "edge.pptx", "x", ["y"], edge)))
    assert r["ok"] and any("살짝 넘은" in m for m in r["warns"]), r

    def tiny(p, s):
        t = s.shapes.add_textbox(Inches(1), Inches(5), Inches(3), Inches(0.5))
        t.text_frame.text = "각주"
        t.text_frame.paragraphs[0].runs[0].font.size = Pt(7)
    r = vop.verify(str(_pptx(tmp_path / "tiny.pptx", "x", ["y"], tiny)))
    assert r["ok"] and any("글자 크기" in m for m in r["warns"]), r

    bad = tmp_path / "rel.pptx"                            # 관계 대상 파트 없음 = PowerPoint 복구 창
    _rewrite(a, bad, {"ppt/slides/slide1.xml": None})
    r = vop.verify(str(bad))
    assert not r["ok"] and any("관계 대상 없음" in m for m in r["fails"]), r


# ── XLSX ─────────────────────────────────────────────────────────────────
def _xlsx(path, rows, formula=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "data"
    for r in rows:
        ws.append(r)
    if formula:
        ws["D1"] = formula
    wb.save(str(path))
    return path


def _cache(path, cell, value, err=True):
    """openpyxl 은 수식 결과 캐시를 못 씀 → 시트 XML 에 <v> 를 넣어 «계산된 파일» 을 흉내 낸다."""
    with zipfile.ZipFile(path) as z:
        x = z.read("xl/worksheets/sheet1.xml").decode()
    i = x.index(f'r="{cell}"')
    j = x.index("</c>", i)
    body = x[i + len(f'r="{cell}"'):j].replace("<v></v>", "").replace("<v />", "").replace("<v/>", "")   # openpyxl 의 빈 캐시 제거
    head = x[:i] + (f'r="{cell}" t="e"' if err else f'r="{cell}"') + body
    x2 = head + f"<v>{value}</v>" + x[j:]
    out = path.with_name(path.stem + "_c.xlsx")
    _rewrite(path, out, {"xl/worksheets/sheet1.xml": x2.encode()})
    return out


def test_xlsx_samples_pass_and_defects_fail(tmp_path):
    a = _cache(_xlsx(tmp_path / "a.xlsx", [["월", "매출"], ["1월", 120], ["2월", 135]], "=SUM(B2:B3)"), "D1", "255", err=False)
    b = _xlsx(tmp_path / "b.xlsx", [["코드", "재고", "단위"], ["P-01", 40, "EA"]])
    for f in (a, b):
        r = vop.verify(str(f))
        assert r["ok"] and r["format"] == "xlsx" and not r["fails"] and not r["warns"], r

    nocache = _xlsx(tmp_path / "n.xlsx", [["x", 1], ["y", 2]], "=SUM(B1:B2)")   # 한 번도 계산 안 된 파일
    r = vop.verify(str(nocache))
    assert r["ok"] and any("결과 캐시 없음" in m and "data!D1" in m for m in r["warns"]), r

    err = _cache(_xlsx(tmp_path / "e.xlsx", [["x", 0]], "=1/B1"), "D1", "#DIV/0!")
    r = vop.verify(str(err))
    assert not r["ok"] and any("오류 값" in m and "#DIV/0!" in m for m in r["fails"]), r

    ghost = _xlsx(tmp_path / "g.xlsx", [["x", 1]], "='없는시트'!A1+1")
    r = vop.verify(str(ghost))
    assert not r["ok"] and any("없는 시트" in m and "없는시트" in m for m in r["fails"]), r


# ── HWPX ─────────────────────────────────────────────────────────────────
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"


def _hwpx(path, paras, mimetype=b"application/hwp+zip", drop=(), section=None):
    sec = section or ('<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
                      f'xmlns:hp="{HP}">' + "".join(f"<hp:p><hp:run><hp:t>{t}</hp:t></hp:run></hp:p>" for t in paras)
                      + "</hs:sec>").encode()
    parts = {
        "version.xml": b'<?xml version="1.0"?><hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" major="5"/>',
        "Contents/header.xml": b'<?xml version="1.0"?><hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"/>',
        "Contents/section0.xml": sec,
        "Contents/content.hpf": (b'<?xml version="1.0"?><opf:package xmlns:opf="http://www.idpf.org/2007/opf/"><opf:manifest>'
                                 b'<opf:item id="header" href="Contents/header.xml"/><opf:item id="section0" href="Contents/section0.xml"/>'
                                 b'</opf:manifest><opf:spine><opf:itemref idref="section0"/></opf:spine></opf:package>'),
        "META-INF/container.xml": b'<?xml version="1.0"?><ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container"/>',
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        if mimetype is not None:
            z.writestr(zipfile.ZipInfo("mimetype"), mimetype, compress_type=zipfile.ZIP_STORED)
        for k, v in parts.items():
            if k not in drop:
                z.writestr(k, v)
    return path


def test_hwpx_samples_pass_and_defects_fail(tmp_path):
    for i, paras in enumerate((["회의록", "참석 3명"], ["공문", "수신 각 부서", "시행일 2026-12-01"])):
        r = vop.verify(str(_hwpx(tmp_path / f"s{i}.hwpx", paras)))
        assert r["ok"] and r["format"] == "hwpx" and not r["fails"], r
        assert r["stats"]["paragraphs"] == len(paras)
        assert any("실렌더" in m for m in r["unverified"])          # 한컴 실제 열기는 이 도구가 확인 못 함
    r = vop.verify(str(_hwpx(tmp_path / "m.hwpx", ["x"], mimetype=b"application/zip")))
    assert not r["ok"] and any("mimetype" in m for m in r["fails"]), r
    r = vop.verify(str(_hwpx(tmp_path / "nm.hwpx", ["x"], mimetype=None)))
    assert r["ok"] and any("mimetype 없음" in m for m in r["warns"]), r
    r = vop.verify(str(_hwpx(tmp_path / "ns.hwpx", ["x"], drop=("Contents/section0.xml",))))
    assert not r["ok"] and any("section" in m for m in r["fails"]), r
    r = vop.verify(str(_hwpx(tmp_path / "bx.hwpx", ["x"], section=b"<hs:sec><hp:p>")))
    assert not r["ok"] and any("XML" in m and "section0" in m for m in r["fails"]), r


def test_cli_exit_codes_and_unknown_format(tmp_path):
    good = _hwpx(tmp_path / "g.hwpx", ["가"])
    bad = _hwpx(tmp_path / "b.hwpx", ["가"], drop=("Contents/header.xml",))
    run = lambda f: subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), str(f)], capture_output=True, text=True,
                                   encoding="utf-8", timeout=60)
    g, b = run(good), run(bad)
    assert g.returncode == 0 and json.loads(g.stdout)[0]["ok"]
    assert b.returncode == 1 and not json.loads(b.stdout)[0]["ok"]
    (tmp_path / "x.txt").write_text("hi", encoding="utf-8")
    r = vop.verify(str(tmp_path / "x.txt"))
    assert not r["ok"] and "지원하지 않는 형식" in r["fails"][0]
    (tmp_path / "z.pptx").write_bytes(b"not a zip")
    r = vop.verify(str(tmp_path / "z.pptx"))
    assert not r["ok"] and "zip" in r["fails"][0]
