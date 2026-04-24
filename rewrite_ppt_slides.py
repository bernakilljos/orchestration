#!/usr/bin/env python3
"""
PPT 25 슬라이드 내용 전면 재작성
Before: 14일 여정 내러티브
After: 설치 후 설계 구조 레퍼런스
"""

import re
from pathlib import Path

def read_html(slide_num):
    return Path(f"outputs/ppt/html-source/slides/slide-{slide_num:02d}.html").read_text(encoding='utf-8')

def write_html(slide_num, content):
    Path(f"outputs/ppt/html-source/slides/slide-{slide_num:02d}.html").write_text(content, encoding='utf-8')

# Slide 01 (Cover)
print("Rewriting Slide 01...")
html = read_html(1)
html = re.sub(
    r'A Developer\'s Journey · 14 Days \+ Opus 4\.7',
    'Installed Architecture Reference',
    html
)
html = re.sub(
    r'Claude Opus 4\.7 · Codex · Haiku 4\.5 · Gemini<br>\s+하나의 엔진 위에 자라난 25개 플러그인의 기록\.',
    'Multi-AI Orchestration · 25 Plugins · SQLite State<br>설치 후 프로젝트 구조 이해하기.',
    html
)
write_html(1, html)

# Slide 02 (설치하면 무엇이 생기나)
print("Rewriting Slide 02...")
html = read_html(2)
html = re.sub(
    r'PART 01 · YOUR DESIGN · THE 14-DAY JOURNEY',
    'PART 01 · INSTALLED STRUCTURE',
    html
)
html = re.sub(
    r'<h1 class="heading-1">14일의 여정</h1>',
    '<h1 class="heading-1">설치하면 무엇이 생기나</h1>',
    html
)
html = re.sub(
    r'<p class="heading-2[^>]*>당신의 설계가 프레임워크가 되기까지</p>',
    '<p class="heading-2 text-stone" style="font-weight: 400;">install.sh / install.bat 실행 직후 프로젝트 구조</p>',
    html
)

# Mermaid 제거 + 본문 추가
body_text = """<p class="body-lead" style="margin-top: 0;">install 스크립트는 프로젝트 루트에 3개의 핵심 폴더와 1개의 AI 규칙 파일을 배치한다. <strong>`.claude/` (Claude Code 런타임), `plugins/` (25개 플러그인 원본), `docs/` (문서), 그리고 최상위에 `CLAUDE.md` (AI 지시서).</strong></p>

<p class="body-text">`.claude-plugin/` 은 Claude Code 의 네이티브 플러그인 매니페스트가 들어간다. `setup/` 은 Windows 인스톨러(Inno Setup) 빌드. `install_codex.bat` · `install_gemini.bat` 은 Claude 없는 standalone 모드 설치용.</p>

<p class="body-text">설치 과정 5단계: (1) 폴더 생성·권한 부여, (2) `.claude/` 파일 복사, (3) `CLAUDE.md` 배포, (4) `.claude/scripts/init-state-db.py` 로 SQLite 초기화, (5) 환경변수 검증.</p>"""

html = re.sub(
    r'<div class="mermaid-wrapper">.*?</div>\s*<p class="body-lead"[^>]*>.*?</p>',
    body_text,
    html,
    flags=re.DOTALL
)

# Bullets
bullets_html = """<h3>◆ INSTALLED ROOT</h3>
<ul>
<li>● `.claude/` — 런타임</li>
<li>● `.claude-plugin/` — 매니페스트</li>
<li>● `plugins/` — 25개 원본</li>
<li>● `docs/` — 가이드·문서</li>
<li>● `CLAUDE.md` — AI 규칙</li>
<li>● `guide.txt` — 사람용 가이드</li>
<li>────────────</li>
<li>Install time · ~30s</li>
</ul>"""

html = re.sub(
    r'<div class="bullet-box">.*?</div>\s*</div>',
    f'<div class="bullet-box">{bullets_html}</div>\n    </div>',
    html,
    flags=re.DOTALL
)

html = re.sub(
    r'<span class="footnote">.*?</span>',
    '<span class="footnote">참조: .claude/ · plugins/ 원본 · CLAUDE.md</span>',
    html
)

write_html(2, html)

print("✓ Slide 01-02 done")
print("Next: Run python generate-final-ppt.py")
