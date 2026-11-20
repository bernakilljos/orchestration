#!/usr/bin/env bash
# pre-commit-full-check.sh — git commit 시 모든 갱신 의무 점검
# 기존 pre-commit-infra-check.sh 를 대체하는 종합 버전
# PreToolUse Bash (git commit 감지) 에서 실행
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

INPUT=$(cat 2>/dev/null || echo '{}')
# 11-15(사이클 1038): 옛 방식('"command":"[^"]*"')은 명령 안의 첫 \" 에서 잘려, git commit 앞에 따옴표가 있으면
#   여기서 exit 0 — 파이썬 디스패처가 커밋으로 넘겨도 회귀 게이트·동반 검사를 통째로 건너뛰었다. JSON 파싱이 정본.
CMD=""
command -v jq >/dev/null 2>&1 && CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
[ -z "$CMD" ] && CMD=$(printf '%s' "$INPUT" | python -X utf8 -c "import json,sys
try: print(json.load(sys.stdin).get('tool_input',{}).get('command',''))
except Exception: pass" 2>/dev/null)
[ -z "$CMD" ] && CMD=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//' 2>/dev/null || echo "")

# git commit 아니면 skip
echo "$CMD" | grep -qE 'git\s+commit' || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 0

STAGED=$(git diff --cached --name-only 2>/dev/null)
MISSING=""

# 1. plugins/hooks/scripts 변경 -> guide.txt 필수
if echo "$STAGED" | grep -qE '^(plugins/|\.claude/hooks/|\.claude/scripts/|setup/)'; then
  echo "$STAGED" | grep -q "^guide.txt" || MISSING="$MISSING\n  - guide.txt (§6-§12-§17)"
  # 2026-10-09: 통계가 이미 최신이면 CLAUDE.md 는 바뀔 게 없어 stage 할 수 없는데도 늘 요구해, 같은 날 두 번째
  #   스크립트 수정 커밋이 매번 막혔다. 통계를 다시 계산해 CLAUDE.md 가 실제로 바뀔 때(또는 바뀐 채 stage 안 됐을 때)만 요구한다.
  if ! echo "$STAGED" | grep -q "^CLAUDE.md"; then
    [ -f .claude/scripts/auto-update-stats.sh ] && bash .claude/scripts/auto-update-stats.sh >/dev/null 2>&1
    git diff --quiet -- CLAUDE.md 2>/dev/null || MISSING="$MISSING\n  - CLAUDE.md (AUTO-STATS 라인 — 방금 auto-update-stats.sh 로 갱신했으니 git add CLAUDE.md)"
  fi
fi

# 2. 플러그인 manifest -> marketplace.json (R350 · 2026-11-20: 종전엔 plugin.json 이 조금만 바뀌어도 marketplace 를 요구해
#    버전을 억지로 올리게 만들었고, 그 JSON 변경이 회귀 게이트를 다시 돌게 했다 → 스테이징된 manifest 와 marketplace 항목을
#    대조해 실제로 어긋날 때(미등록·버전 다름)만 요구 · 둘 다 index(스테이징) 내용으로 비교)
PLUGINS_CHANGED=$(echo "$STAGED" | grep -E '^plugins/[^/]+/plugin\.json$')
if [ -n "$PLUGINS_CHANGED" ]; then
  MP_ISSUES=$(printf '%s\n' "$PLUGINS_CHANGED" | python -X utf8 -c "import json,subprocess,sys
def show(p):
    r=subprocess.run(['git','show',':'+p],capture_output=True,text=True,encoding='utf-8',errors='replace')
    return json.loads(r.stdout) if r.returncode==0 else None
mp=show('.claude-plugin/marketplace.json') or {}
idx={x.get('name'):x for x in mp.get('plugins',[]) if isinstance(x,dict)}
for p in sys.stdin.read().split():
    m=show(p)
    if not m: continue
    e=idx.get(m.get('name'))
    if e is None: print('%s 미등록'%m.get('name'))
    elif str(e.get('version'))!=str(m.get('version')): print('%s 버전 %s != manifest %s'%(m.get('name'),e.get('version'),m.get('version')))" 2>/dev/null)
  [ -n "$MP_ISSUES" ] && MISSING="$MISSING\n  - .claude-plugin/marketplace.json ($(echo "$MP_ISSUES" | tr -d '\r' | tr '\n' ' ' | sed 's/ $//'))"
fi

# 3. 새 hook (Added only — Modified bug-fixes 는 settings.json 등록 불필요) -> settings.json
NEW_HOOK=$(git diff --cached --diff-filter=A --name-only 2>/dev/null | grep -E '^(plugins|\.claude)/.*hooks/.*\.sh$' | head -1)
if [ -n "$NEW_HOOK" ]; then
  echo "$STAGED" | grep -q "settings.json" || MISSING="$MISSING\n  - .claude/settings.json (hook 등록)"
fi

# 4. setup 모듈 변경 -> BUILD.md
if echo "$STAGED" | grep -qE '^setup/modules/'; then
  echo "$STAGED" | grep -q "BUILD.md" || MISSING="$MISSING\n  - setup/BUILD.md (모듈 설명)"
fi

# 5. 레퍼런스 추가 -> sync 실행 확인 (sync 는 commit 전 수동)
# (placeholder — no-op)

# 6. 코드 변경 -> 회귀 방지 게이트 기록이 지금 스테이징 내용과 같아야 (2026-11-09 · A 수정으로 B·C 가 깨지는 것 차단)
#    시험은 훅 시간(5초) 안에 못 돌리므로 regression-gate 가 남긴 기록의 트리 해시·상태만 확인한다.
#    확장자 목록 = independent_verifier._CODE_EXT (2026-11-15 R256: vue·jsx·mjs·cjs·json·java·xml·yml·go 가 빠져
#    게이트가 검사 대상으로 보는 파일만 바꾼 커밋은 이 훅이 게이트를 요구하지 않았다 · 시험이 두 목록을 대조)
#    PRECOMMIT_PREFLIGHT=1 (R350): 회귀 게이트가 시험 전에 이 훅을 미리보기로 불러 동반 파일 누락을 먼저 한 번에 받는다 — 이때는 게이트 자신을 검사하지 않음
if [ "${PRECOMMIT_PREFLIGHT:-0}" != 1 ] && echo "$STAGED" | grep -qiE '\.(py|sh|ps1|psm1|bat|cmd|js|ts|tsx|vue|jsx|mjs|cjs|json|java|xml|yml|yaml|go)$' && [ -f .claude/scripts/lib/independent_verifier.py ]; then
  TREE=$(git write-tree 2>/dev/null || echo "")
  PYBIN=$(command -v python || command -v python3 || echo "")
  if [ -n "$TREE" ] && [ -n "$PYBIN" ]; then
    # 트리가 달라도 코드 파일 지문(code_tree)이 같으면 문서만 더 stage 한 것 — 시험을 다시 돌릴 이유가 없다
    #   (lottoclaude 11-16 21:40: CLAUDE.md AUTO-STATS 날짜 한 줄 때문에 7분 전체 회귀를 재실행하다 dev 회차 61분 시간 초과).
    GATE=$("$PYBIN" -X utf8 -c "import json,sys,subprocess,hashlib
try: d=json.load(open('.claude/state/regression-gate.json',encoding='utf-8'))
except Exception: print('none'); sys.exit()
if d.get('tree')==sys.argv[1]: print(d.get('status')); sys.exit()
ext=('.py','.sh','.ps1','.psm1','.bat','.cmd','.js','.ts','.tsx','.vue','.jsx','.mjs','.cjs','.json','.java','.xml','.yml','.yaml','.go')
out=subprocess.run(['git','-c','core.quotepath=off','ls-files','-s'],capture_output=True,text=True,encoding='utf-8',errors='replace').stdout
rows=[l for l in out.splitlines() if l.split('\t')[-1].lower().endswith(ext)]
fp=hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest() if rows else ''
print(d.get('status') if fp and d.get('code_tree')==fp else 'stale')" "$TREE" 2>/dev/null || echo "none")
    case "$GATE" in
      pass|preexisting|skip) ;;
      syntax_error) MISSING="$MISSING\n  - 변경 소스 문법 오류: .claude/state/regression-gate.json 의 syntax_errors 파일을 고친 뒤 regression-gate 다시 실행" ;;
      unverified) MISSING="$MISSING\n  - 문법 검사기가 없어 확인 못 한 변경 파일 (.claude/state/regression-gate.json 의 syntax_unchecked) — 검증 완료로 보지 않아 자동 커밋하지 않음 · 사용자가 직접 확인 후 커밋" ;;
      regression) MISSING="$MISSING\n  - 회귀 발견: 수정 전 통과하던 시험이 실패 — .claude/state/regression-gate.json 의 new_failures 원인 수정 후 다시 실행" ;;
      perf_regression|perf_unmeasured) MISSING="$MISSING\n  - 속도 검사 실패 ($GATE): .claude/state/regression-gate.json 의 perf.items 에서 느려진 항목(기준선·상한) 확인 → 원인 고친 뒤 regression-gate 다시 실행" ;;
      *) MISSING="$MISSING\n  - 회귀 방지 게이트 ($GATE): python -X utf8 .claude/scripts/lib/independent_verifier.py regression-gate 실행 후 커밋 (스테이징을 바꾸면 다시)" ;;
    esac
  fi
fi

# 7. 상태줄 코드 변경 -> Design Ownership Lock (R275 · 승인 구조 = .claude/design-baseline/statusline.json)
#    구조가 바뀌었는데 해제(design-gate.py unlock statusline <사유>) 기록이 없으면 커밋 차단 · 렌더 실패는 미측정(차단 X)
if echo "$STAGED" | grep -qE '(^|/)statusline_context\.py$' && [ -f .claude/scripts/design-gate.py ] && [ -f .claude/design-baseline/statusline.json ]; then
  PYBIN=$(command -v python || command -v python3 || echo "")
  if [ -n "$PYBIN" ]; then
    DG_OUT=$("$PYBIN" -X utf8 .claude/scripts/design-gate.py check statusline 2>&1)
    [ $? -eq 2 ] && MISSING="$MISSING\n  - 상태줄 승인 구조와 다름 (해제 없이 바뀜 = 임의변경): $(echo "$DG_OUT" | head -3 | tr '\n' ' ')"
  fi
fi

if [ -n "$MISSING" ]; then
  # 사유는 stderr 로 — exit 2 일 때 Claude 에게 돌아가는 것은 stderr 뿐 (2026-10-16, stdout 이라 사유가 사라졌다)
  cat >&2 <<MSG

[X] [BLOCK] 커밋 시 갱신 누락 감지!

  다음 파일을 같이 stage 하세요:
$(echo -e "$MISSING")

  배포용 솔루션 규칙: 기능 변경과 관련 문서는 같은 커밋에.
  bugfix 라도 guide.txt 해당 절에 한 줄(무엇이 왜 바뀌었나) 을 적고 같이 stage 한다 — --no-verify 금지.

MSG
  exit 2
fi

exit 0
