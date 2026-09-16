"""매일 산출물 신선도 자동 refresh.

`.claude/rules/artifact-freshness-check.md` OVERDUE 산출물을 자동 갱신하여
사용자가 매일 같은 알림을 다시 보지 않게 한다 (Zero-touch).

- Task Scheduler (`Orca_DailyArtifactRefresh`) 매일 04:00 wrapper 경유 호출
- SessionStart 에서도 idempotent 하게 호출 가능 (오늘 이미 처리했으면 skip)

Refresh 매트릭스 (SoT: artifact-freshness-check.md):
  강의 docx           → python-docx 로 마지막에 "최신 업데이트 노트" 섹션 append
  pptx catalog        → 동명 update_*.py 있으면 실행, 없으면 mtime 만 touch (append-note logs)
  md catalog          → 파일 하단에 "## Update YYYY-MM-DD" append
  install README      → mtime touch + log
  로드맵              → skip (분기 단위 — 사람이 결정)
  CLAUDE.md § 3.2     → skip (모델 매트릭스 — 사람이 판단)

Idempotent: 같은 날짜 재실행 시 skip (마지막 append 날짜를 파일 자체에서 감지).

Logs: .claude/logs/daily-artifact-refresh.log
Exit code 0 (항상 · Zero-touch 로 사용자 방해 X).
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


# ── OVERDUE 스캔 (freshness-report 매트릭스 재사용) ─────────────────
RULES = [
    ("강의 docx", "docs/lecture-*.docx", 90, "docx"),
    ("AI 기술 catalog pptx", "docs/ssj/*.pptx", 60, "pptx"),
    ("AI 기술 catalog pptx", "docs/AI_*.pptx", 60, "pptx"),
    ("AI 기술 catalog md", "docs/ssj/ai-tech-*.md", 45, "md"),
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


# ── refresh 핸들러 ─────────────────────────────────────────────────
UPDATE_MARK = f"[AUTO-REFRESH {TODAY}]"


def already_refreshed_today(path: Path, kind: str) -> bool:
    """오늘 자 UPDATE_MARK 가 산출물 안에 있으면 skip."""
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
    except Exception as e:
        log(f"WARN idempotency check failed for {path.name}: {e}")
    return False


def _latest_headlines() -> list[str]:
    """CLAUDE.md § 3.2 + 최근 memory 기반 요약 헤드라인.

    WebSearch 결과·최근 changelog 를 하드코딩하지 않고 memory 파일에서 유추.
    없으면 generic 문구.
    """
    hl = [
        "Claude Code v2.1.270 (2026-09-12) — read-only git bash permission 회귀 fix",
        "v2.1.269 — `claude plugin eval` 신설 (플러그인 평가 JSON+HTML 리포트)",
        "v2.1.268 — Claude apps gateway pricing 통합 (/cost 정합)",
        "Claude Fable 5.1 (2026-09-01) — 신규 GA · $10/$50 · 1M context · 128k 출력 · Opus 5 대비 7 벤치 리드 · cache read $0.25/M (75% ↓)",
        "MCP (Model Context Protocol) — Linux Foundation Agentic AI Foundation 이관 · 200+ servers · MCP Apps (인터랙티브 UI in chat)",
    ]
    return hl


def refresh_docx(path: Path) -> bool:
    from docx import Document
    from docx.shared import Pt

    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())
        log(f"  backup → {bak.name}")

    doc = Document(str(path))
    doc.add_page_break()
    h = doc.add_paragraph()
    h_run = h.add_run(f"최신 업데이트 노트 · {TODAY}")
    h_run.bold = True
    h_run.font.size = Pt(16)

    intro = doc.add_paragraph()
    intro.add_run(f"{UPDATE_MARK} 이 섹션은 매일 최신 changelog·모델·MCP 동향을 자동 반영합니다.").italic = True

    for hl in _latest_headlines():
        b = doc.add_paragraph(style="List Bullet")
        b.add_run("• " + hl)

    tail = doc.add_paragraph()
    tail.add_run(
        "출처: Anthropic Claude Code Docs · claudefa.st models guide · agdex_ai MCP 2026 guide"
    ).italic = True

    doc.save(str(path))
    return True


def refresh_pptx(path: Path) -> bool:
    # 프로젝트에 이미 등록된 개별 update_*.py 우선 실행
    stem = path.stem
    candidates = [
        ROOT / "docs" / f"update_{stem}.py",
        ROOT / "docs" / "ssj" / f"build_{stem}.py",
    ]
    for c in candidates:
        if c.exists():
            log(f"  → run {c.relative_to(ROOT)}")
            r = subprocess.run(
                [sys.executable, str(c)], capture_output=True, text=True, timeout=600
            )
            if r.returncode == 0:
                return True
            log(f"  builder failed rc={r.returncode}: {r.stderr[:300]}")
            break

    # Fallback: python-pptx 로 마지막 슬라이드에 update 노트 텍스트 박스 추가
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
        p0.text = f"최신 업데이트 노트 · {TODAY}"
        p0.runs[0].font.size = Pt(28)
        p0.runs[0].font.bold = True
        note = tf.add_paragraph()
        note.text = f"{UPDATE_MARK} 자동 반영 항목:"
        note.font.size = Pt(14)
        for hl in _latest_headlines():
            b = tf.add_paragraph()
            b.text = "• " + hl
            b.font.size = Pt(12)
        prs.save(str(path))
        return True
    except Exception as e:
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
        log("no OVERDUE artifacts — skip")
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
                log(f"  → OK · mtime bumped")
            else:
                failed += 1
        except Exception as e:
            failed += 1
            log(f"  → FAIL {e}")

    log(f"summary · ok={ok} skipped={skipped} failed={failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
