#!/usr/bin/env python3
"""자동 생성한 스킬 frontmatter 롤백 (사용자 수동 편집분 보존)

원칙:
  - 내가 추가한 generic frontmatter (48개) → 제거
  - 사용자가 수동 편집한 파일 → 보존 (SKIP)
  - 기준: frontmatter description 에 '관련 키워드 언급 시 또는' 문구가 있으면 자동 생성물
"""
import sys, re
from pathlib import Path

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

# 사용자 수동 편집 확인된 파일 (system-reminder 기록) — 절대 건드리지 않음
PROTECT = {
    "plugins/exec_orch/skills/route_dispatch.md",
    "plugins/design_ppt/skills/skill-16-brand-guidelines.md",
    "plugins/design_ppt/skills/skill-15-theme-factory.md",
    "plugins/exec_session_guard/skills/skill-token-tracker.md",
}

# 자동 생성 frontmatter 특징 — 이 문구 포함 시 내가 만든 거
AUTO_MARKER = "관련 키워드 언급 시 또는"

plugins_dir = Path("plugins")
removed = 0
kept_user = 0
skipped = 0

for p in plugins_dir.iterdir():
    if not p.is_dir() or p.name.startswith("_"):
        continue
    skills_dir = p / "skills"
    if not skills_dir.exists():
        continue

    for skill_file in skills_dir.glob("*.md"):
        rel = f"plugins/{p.name}/skills/{skill_file.name}"
        if rel in PROTECT:
            kept_user += 1
            continue

        txt = skill_file.read_text(encoding="utf-8")
        if not txt.startswith("---\n"):
            skipped += 1
            continue

        # frontmatter 범위 찾기
        m = re.match(r"^---\n(.*?)\n---\n\n?", txt, re.DOTALL)
        if not m:
            skipped += 1
            continue

        fm_content = m.group(1)
        # 자동 생성 marker 확인
        if AUTO_MARKER not in fm_content:
            # 사용자가 직접 쓴 frontmatter (보존)
            kept_user += 1
            continue

        # 자동 생성물 — frontmatter 제거
        new_txt = txt[m.end():]
        skill_file.write_text(new_txt, encoding="utf-8")
        removed += 1

print(f"✓ 자동 생성 frontmatter 제거: {removed} 파일")
print(f"✓ 사용자 편집 보존: {kept_user} 파일")
print(f"✓ 대상 아님 (frontmatter 없음): {skipped} 파일")
