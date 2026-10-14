"""plugins/exec_orch/hooks/pre-build-reminder.sh 이식 - 빌더 명령(build/generate/render-*.py) 실행 전 reminder (systemMessage)."""
from __future__ import annotations

import re

from _common import Result, Spawn, bash_cat, grep_o_first, has_jq

REL = "plugins/exec_orch/hooks/pre-build-reminder.sh"
_BUILD = re.compile(r"(build|generate|render)-[a-z-]+-(ppt|doc|diagrams|pdf|html)\.py|build-[a-z-]+-doc\.py")
_SED = re.compile(r'.*:"(.*)"')
MSG = '{\n  "systemMessage": "[pre-build] 빌드 전 5중박기 reminder (놓치면 농땡이):\\n1. 페이지 콘텐츠 fit — H1(0.55) + callout(0.5) + 이미지 ≤ 7.33 inch (landscape A4 사용)\\n2. PNG 비율 = 페이지 비율 (landscape 0.69 / portrait 1.46 / pptx 16:9 0.54)\\n3. 캡션 \'(HTML/CSS+SVG)\' 같은 메타 정보 노출 금지 (사용자 불필요)\\n4. 글씨 가독성 — viewport 작을수록 docx 화면 표시 비율 ↑\\n5. 빌드 후 verify-image-fit + hook-09 자동 검증 — 위반 시 즉시 알림\\n6. PageLayoutTracker 사용 (auto-layout-fit skill) — 자동 max_height 계산\\n7. 산출물 자동 -v2 폴백 X — .bak 백업 후 덮어쓰기\\n8. 잠금 fail 시 60초 폴링 (즉시 sys.exit X)"\n}\n'


def run(ctx):
    if has_jq():
        return Spawn(REL)
    m = grep_o_first(bash_cat(ctx.raw), r'"command"[ \t\r\f\v]*:[ \t\r\f\v]*"[^"]*"')
    cmd = ""
    if m is not None:
        mm = _SED.match(m)
        cmd = mm.group(1) if mm else m
    if not _BUILD.search(cmd):
        return None
    return Result(0, MSG, "")
