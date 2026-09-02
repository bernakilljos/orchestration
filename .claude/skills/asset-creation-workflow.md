---
name: asset-creation-workflow
description: 새 자산 (rule·hook·skill·command·agent·memory) 만들 때 유형별 표준 세트 체크리스트. Windows PowerShell 자매 파일·유사 파일 grep·자매 spec (hook = md + sh) 강제. 감지 hook `.claude/hooks/detect-asset-creation.sh` 자동 발동.
---

# 자산 생성 워크플로우 (유형별 표준 세트)

새 rule·hook·skill·command·agent·memory 만들기 전 이 체크리스트 실행. 감지 hook 이 PreToolUse 로 자동 warn — 무시하면 중복 자산 폭주.

## 공통 절차 (모든 유형)

1. **유사 파일 grep** — `grep -rln "<purpose keyword>" .claude/ plugins/`
2. **정본 위치 확인** — SoT 표 (아래) 대조
3. **자매 파일 유형** — 유형별 표 (아래) 대조
4. **작성** — 표준 frontmatter + 근거·이유·How to apply
5. **인덱스 갱신** — MEMORY.md·CLAUDE.md § 7·rules INDEX (있으면)

## 유형별 표준 세트

| 유형 | 정본 위치 | 자매 파일 | 인덱스 |
|---|---|---|---|
| **rule** | `.claude/rules/<name>.md` 1개 | (없음) | CLAUDE.md § 7 조항 참조 |
| **hook (bash)** | `plugins/*/hooks/<name>.sh` (SoT) → `.claude/hooks/` sync | `<name>.ps1` (Windows) + `<name>.md` (spec) | `.claude/settings.json` hooks 등록 |
| **hook (PowerShell)** | `plugins/*/hooks/<name>.ps1` | `<name>.sh` (Linux/Mac) + `<name>.md` (spec) | 위 |
| **skill** | `plugins/*/skills/<name>.md` | (없음) | 자동 (skill 은 description 기반 활성) |
| **command** | `plugins/*/commands/<name>.md` 1개 | (없음) | sync-plugins.sh 로 `.claude/commands/` fanout |
| **agent** | `plugins/*/agents/agent-<name>.md` | (없음) | 자동 |
| **memory** | `~/.claude/projects/<proj>/memory/feedback_<slug>.md` (하나) | (없음) | `MEMORY.md` 인덱스 라인 |

## Windows/Linux/Mac 자매 규칙 (hook 전용)

hook 은 실행 환경에 따라 다른 셸 필요. 다음 3 유형 커버 원칙:

| 원본 | 자매 필수? | 예시 |
|---|---|---|
| `.sh` (bash) | Windows 사용자 대비 `.ps1` 권장 | `pre-install-lock.sh` → `pre-install-lock.ps1` |
| `.ps1` (PowerShell) | Linux/Mac 대비 `.sh` 권장 | `deploy-vscode-settings.ps1` → `.sh` |
| `.py` (Python) | 자매 불필요 (크로스 플랫폼) | `block_dangerous_bash.py` |

**요청 시만 만들기**: 사용자가 명시 지시 안 하면 `.sh` 만 만들고 `.ps1` skeleton 안내. 자동 폭주 방지 (feedback_common_kit_not_domain 정합).

## 유사 파일 grep 체크리스트

| 자산 유형 | grep 대상 |
|---|---|
| rule | `.claude/rules/*.md` — description·§ heading 유사 |
| hook | `.claude/hooks/*.sh` + `plugins/*/hooks/*.sh` — 목적 keyword |
| skill | `plugins/*/skills/*.md` + `.claude/skills/*.md` — description keyword |
| command | `plugins/*/commands/*.md` + `.claude/commands/*.md` — 이름·별명 |
| memory | `~/.claude/projects/<proj>/memory/*.md` — 주제 keyword |

## 워크플로우 트리거 (감지 hook 발동)

`.claude/hooks/detect-asset-creation.sh` (PreToolUse Write) 이 자동:
1. 새 파일 유형 판정 (경로 패턴 매치)
2. 유사 파일 grep
3. 자매 파일 검사 (`.sh` → `.ps1` 존재?)
4. systemMessage 로 warn (block X — 경고만)

## 금기

1. 유사 파일 grep 없이 신규 생성
2. `.sh` 만 만들고 `.ps1` skeleton 안내 없이 종료 (Windows 사용자 배제)
3. 자산 유형 오분류 (rule 을 skill 로 만듬 등)
4. 인덱스 (MEMORY.md·CLAUDE.md § 7) 갱신 skip

## 관련

- `.claude/rules/consistency.md` § 함수·훅·룰 중복 금지
- `.claude/rules/direction-first.md`
- `.claude/rules/failure-mode.md`
- `feedback_no_duplicate_function.md`
- `feedback_common_kit_not_domain.md`
