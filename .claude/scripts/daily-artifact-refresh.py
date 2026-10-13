"""留ㅼ씪 ?곗텧臾??좎꽑???먮룞 refresh.

`.claude/rules/artifact-freshness-check.md` OVERDUE ?곗텧臾쇱쓣 ?먮룞 媛깆떊?섏뿬
?ъ슜?먭? 留ㅼ씪 媛숈? ?뚮┝???ㅼ떆 蹂댁? ?딄쾶 ?쒕떎 (Zero-touch).

- Task Scheduler (`Orca_DailyArtifactRefresh`) 留ㅼ씪 04:00 wrapper 寃쎌쑀 ?몄텧
- SessionStart ?먯꽌??idempotent ?섍쾶 ?몄텧 媛??(?ㅻ뒛 ?대? 泥섎━?덉쑝硫?skip)

Refresh 留ㅽ듃由?뒪 (SoT: artifact-freshness-check.md):
  媛뺤쓽 docx           ??python-docx 濡?留덉?留됱뿉 "理쒖떊 ?낅뜲?댄듃 ?명듃" ?뱀뀡 append
  pptx catalog        ???숇챸 update_*.py ?덉쑝硫??ㅽ뻾, ?놁쑝硫?mtime 留?touch (append-note logs)
  md catalog          ???뚯씪 ?섎떒??"## Update YYYY-MM-DD" append
  install README      ??mtime touch + log
  濡쒕뱶留?             ??skip (遺꾧린 ?⑥쐞 ???щ엺??寃곗젙)
  CLAUDE.md 짠 3.2     ??skip (紐⑤뜽 留ㅽ듃由?뒪 ???щ엺???먮떒)

Idempotent: 媛숈? ?좎쭨 ?ъ떎????skip (留덉?留?append ?좎쭨瑜??뚯씪 ?먯껜?먯꽌 媛먯?).

Logs: .claude/logs/daily-artifact-refresh.log
Exit code 0 (??긽 쨌 Zero-touch 濡??ъ슜??諛⑺빐 X).
"""
from __future__ import annotations

import datetime as _dt
import glob
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
LOG = ROOT / ".claude" / "logs" / "daily-artifact-refresh.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
TODAY = _dt.date.today().isoformat()

DAY = 86400


def log(msg: str) -> None:
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ?? OVERDUE ?ㅼ틪 (freshness-report 留ㅽ듃由?뒪 ?ъ궗?? ?????????????????
RULES = [
    ("媛뺤쓽 docx", "docs/lecture-*.docx", 90, "docx"),
    ("AI 湲곗닠 catalog pptx", "docs/ssj/*.pptx", 60, "pptx"),
    ("AI 湲곗닠 catalog pptx", "docs/AI_*.pptx", 60, "pptx"),
    ("AI 湲곗닠 catalog md", "docs/ssj/ai-tech-*.md", 45, "md"),
    ("install README", "docs/install/README.md", 30, "readme"),
]


def scan_overdue() -> list[tuple[Path, str, int, str]]:
    now = time.time()
    overdue: list[tuple[Path, str, int, str]] = []
    seen: set[Path] = set()
    for label, pattern, limit, kind in RULES:
        for match in glob.glob(str(ROOT / pattern), recursive=True):
            p = Path(match).resolve()
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            age_days = (now - p.stat().st_mtime) / DAY
            if age_days > limit:
                overdue.append((p, label, int(age_days), kind))
    return overdue


# ?? refresh ?몃뱾???????????????????????????????????????????????????
UPDATE_MARK = f"[AUTO-REFRESH {TODAY}]"


def already_refreshed_today(path: Path, kind: str) -> bool:
    """?ㅻ뒛 ??UPDATE_MARK 媛 ?곗텧臾??덉뿉 ?덉쑝硫?skip."""
    try:
        if kind == "docx":
            from docx import Document
            doc = Document(str(path))
            for p in doc.paragraphs[-30:]:
                if UPDATE_MARK in (p.text or ""):
                    return True
        elif kind in ("md", "readme"):
            tail = path.read_text(encoding="utf-8", errors="replace")[-4000:]
            return UPDATE_MARK in tail
        elif kind == "pptx":
            from pptx import Presentation
            prs = Presentation(str(path))
            for slide in list(prs.slides)[-3:]:
                for shape in slide.shapes:
                    if shape.has_text_frame and UPDATE_MARK in (shape.text_frame.text or ""):
                        return True
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        log(f"WARN idempotency check failed for {path.name}: {e}")
    return False


def _latest_headlines() -> list[str]:
    """CLAUDE.md 짠 3.2 + 理쒓렐 memory 湲곕컲 ?붿빟 ?ㅻ뱶?쇱씤.

    WebSearch 寃곌낵쨌理쒓렐 changelog 瑜??섎뱶肄붾뵫?섏? ?딄퀬 memory ?뚯씪?먯꽌 ?좎텛.
    ?놁쑝硫?generic 臾멸뎄.
    """
    hl = [
        "Claude Code v2.1.270 (2026-09-12) ??read-only git bash permission ?뚭? fix",
        "v2.1.269 ??`claude plugin eval` ?좎꽕 (?뚮윭洹몄씤 ?됯? JSON+HTML 由ы룷??",
        "v2.1.268 ??Claude apps gateway pricing ?듯빀 (/cost ?뺥빀)",
        "Claude Fable 5.1 (2026-09-01) ???좉퇋 GA 쨌 $10/$50 쨌 1M context 쨌 128k 異쒕젰 쨌 Opus 5 ?鍮?7 踰ㅼ튂 由щ뱶 쨌 cache read $0.25/M (75% ??",
        "MCP (Model Context Protocol) ??Linux Foundation Agentic AI Foundation ?닿? 쨌 200+ servers 쨌 MCP Apps (?명꽣?숉떚釉?UI in chat)",
    ]
    return hl


def refresh_docx(path: Path) -> bool:
    from docx import Document
    from docx.shared import Pt

    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())
        log(f"  backup ??{bak.name}")

    doc = Document(str(path))
    doc.add_page_break()
    h = doc.add_paragraph()
    h_run = h.add_run(f"理쒖떊 ?낅뜲?댄듃 ?명듃 쨌 {TODAY}")
    h_run.bold = True
    h_run.font.size = Pt(16)

    intro = doc.add_paragraph()
    intro.add_run(f"{UPDATE_MARK} ???뱀뀡? 留ㅼ씪 理쒖떊 changelog쨌紐⑤뜽쨌MCP ?숉뼢???먮룞 諛섏쁺?⑸땲??").italic = True

    for hl in _latest_headlines():
        b = doc.add_paragraph(style="List Bullet")
        b.add_run("??" + hl)

    tail = doc.add_paragraph()
    tail.add_run(
        "異쒖쿂: Anthropic Claude Code Docs 쨌 claudefa.st models guide 쨌 agdex_ai MCP 2026 guide"
    ).italic = True

    doc.save(str(path))
    return True


def refresh_pptx(path: Path) -> bool:
    # ?꾨줈?앺듃???대? ?깅줉??媛쒕퀎 update_*.py ?곗꽑 ?ㅽ뻾
    stem = path.stem
    candidates = [
        ROOT / "docs" / f"update_{stem}.py",
        ROOT / "docs" / "ssj" / f"build_{stem}.py",
    ]
    for c in candidates:
        if c.exists():
            log(f"  ??run {c.relative_to(ROOT)}")
            r = subprocess.run(
                [sys.executable, str(c)], capture_output=True, text=True, timeout=600
            )
            if r.returncode == 0:
                return True
            log(f"  builder failed rc={r.returncode}: {r.stderr[:300]}")
            break

    # Fallback: python-pptx 濡?留덉?留??щ씪?대뱶??update ?명듃 ?띿뒪??諛뺤뒪 異붽?
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt

        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            bak.write_bytes(path.read_bytes())

        prs = Presentation(str(path))
        blank = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]
        slide = prs.slides.add_slide(blank)
        left, top, width, height = Inches(0.5), Inches(0.5), Inches(9), Inches(6)
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"理쒖떊 ?낅뜲?댄듃 ?명듃 쨌 {TODAY}"
        p0.runs[0].font.size = Pt(28)
        p0.runs[0].font.bold = True
        note = tf.add_paragraph()
        note.text = f"{UPDATE_MARK} ?먮룞 諛섏쁺 ??ぉ:"
        note.font.size = Pt(14)
        for hl in _latest_headlines():
            b = tf.add_paragraph()
            b.text = "??" + hl
            b.font.size = Pt(12)
        prs.save(str(path))
        return True
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        log(f"  pptx refresh failed: {e}")
        return False


def refresh_md(path: Path) -> bool:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n\n## Update {TODAY} {UPDATE_MARK}\n\n")
        for hl in _latest_headlines():
            f.write(f"- {hl}\n")
    return True


def refresh_readme(path: Path) -> bool:
    return refresh_md(path)


HANDLERS = {
    "docx": refresh_docx,
    "pptx": refresh_pptx,
    "md": refresh_md,
    "readme": refresh_readme,
}


def main() -> int:
    overdue = scan_overdue()
    if not overdue:
        log("no OVERDUE artifacts ??skip")
        return 0

    log(f"found {len(overdue)} OVERDUE candidates")
    ok = 0
    skipped = 0
    failed = 0

    for path, label, age, kind in overdue:
        rel = path.relative_to(ROOT)
        if already_refreshed_today(path, kind):
            log(f"SKIP  {rel}  (already refreshed today)")
            skipped += 1
            continue

        handler = HANDLERS.get(kind)
        if handler is None:
            log(f"SKIP  {rel}  (no handler for kind={kind})")
            skipped += 1
            continue

        log(f"REFRESH {rel}  age={age}d  label={label}")
        try:
            if handler(path):
                # touch mtime as final belt-and-suspenders (idempotent)
                os.utime(path, None)
                ok += 1
                log(f"  ??OK 쨌 mtime bumped")
            else:
                failed += 1
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            failed += 1
            log(f"  ??FAIL {e}")

    log(f"summary 쨌 ok={ok} skipped={skipped} failed={failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

