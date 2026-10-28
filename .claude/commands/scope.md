---
description: 요청 범위 lock — 지정 glob 외 파일 Edit·Write 시 WARN (opt-in · 24h 자동 만료)
allowed-tools: Bash(python:*)
---

# /scope — 요청 범위 lock

사용자가 "A·B 만 손대" 지시했을 때 범위 밖 수정을 WARN 또는 DENY 로 막는다.
기본은 비활성 — 명시 활성화 시만 발동. 24h 자동 만료.

## 사용

```bash
# 활성화 (glob 하나 이상)
python .claude/scripts/scope-lock.py activate "plugins/exec_orch/**/*" ".claude/rules/*.md"

# 상태 확인
python .claude/scripts/scope-lock.py status

# 모드 변경 (warn | deny)
python .claude/scripts/scope-lock.py mode deny

# 수동 체크
python .claude/scripts/scope-lock.py check path/to/file.py

# 해제
python .claude/scripts/scope-lock.py deactivate
```

## 모드

- **warn** (기본): 범위 외 수정 시 systemMessage 로 경고. 수정은 통과.
- **deny**: 범위 외 수정 시 exit 2 로 차단.

## 왜 opt-in · 1주 WARN

사용자 프롬프트에서 "범위 어휘" 자동 추출 (B안) 은 regex 가 틀리면 cascade (lib·import·sibling) 다 block.
1주 WARN 로그 보고 패턴 확인 후 B안 (auto) 로 고도화.

## 관련

- `.claude/scripts/scope-lock.py` — CLI 핸들러
- `.claude/hooks/tool/scope_lock.py` — PreToolUse 모듈 (Edit·Write)
- `.claude/state/scope-lock.json` — 상태 (24h TTL)
