# Hook 스코프 분리 룰 (Hook Scope Separation)

> **근거**: 2026-09-02 사용자 지적 — "hook 프로젝트별로 분리 안 됨 · 전용 전역 개선".
> **이유**: hook 스코프 (프로젝트 vs 전역 vs 플러그인) 명확 · 다른 프로젝트 오염 방지.

## 절대 룰

**우리 kit hook 은 프로젝트 (`.claude/settings.json`) 전용. 전역 (`~/.claude/settings.json`) 에 kit hook 등록 금지.**

## 3 스코프 매트릭스

| 스코프 | 위치 | 대상 | 예시 |
|---|---|---|---|
| **프로젝트** | `.claude/settings.json` | 이 프로젝트만 · `plugins/` 존재 시 발동 | 우리 kit 모든 hook (72개+) |
| **전역** | `~/.claude/settings.json` | 모든 프로젝트 · 최소만 | Claude Code 기본 · language·theme·permissions |
| **플러그인** | plugin marketplace 관리 | 플러그인별 자동 | claude-mem (5 hook)·commit-commands·claude-md-management |

## 우리 kit hook 원칙

1. **프로젝트 전용**: `.claude/settings.json` 만 등록
2. **guard 필수**: hook script 안 `[ -d plugins ] || exit 0` 조건 (다른 프로젝트에서 skip)
3. **경로 상대**: `$CLAUDE_PROJECT_DIR` 사용 (하드코딩 X)
4. **전역 등록 금지**: `~/.claude/settings.json` 에 kit hook 넣지 X

## 전역 등록 허용 (예외 · 최소만)

| 항목 | 이유 |
|---|---|
| Claude Code 기본 설정 (language·theme·checkpointingEnabled) | 모든 프로젝트 공통 |
| Official plugins (claude-md-management·commit-commands·superpowers) | Anthropic 공식 · 검증됨 |
| Marketplace plugins (claude-mem·plugin) | plugin marketplace 자동 관리 |

## Guard 패턴 (우리 kit hook 표준)

```bash
#!/usr/bin/env bash
# Sub-project guard: 다른 프로젝트에서 이 hook 이 실행되어도 skip
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
```

= plugins 폴더 없는 프로젝트 (target·설정·글로벌) 에서 우리 hook 이 등록되어 있어도 즉시 exit 0 · 무해.

## 검증 스크립트

`.claude/scripts/verify-hook-scope.py`:
- `~/.claude/settings.json` 확인 · kit hook 유출 감지
- kit hook script 안 guard 존재 여부
- 문제 발견 시 경고

실행: `python .claude/scripts/verify-hook-scope.py`

## Install 시 자동 확인

`setup/modules/03-settings.bat` 확장:
- 전역 settings 배포 시 우리 kit hook 등록 X 검증
- 프로젝트 settings 만 kit hook 반영

## 다른 프로젝트에서 우리 kit hook 발동 시 (사고 시나리오)

- 예: 우리 kit hook 이 실수로 `~/.claude/settings.json` 에 등록됨
- 사용자가 다른 프로젝트 열면 우리 hook 이 발동 시도
- guard 로 즉시 skip · 무해 · 하지만 overhead 있음
- **완전 방지 = 전역 등록 자체 하지 X**

## 우리 kit 이 이미 정합 (2026-09-02 실측)

- `~/.claude/settings.json`: hooks 없음 ✅
- `.claude/settings.json`: 72+ hooks (프로젝트 전용) ✅
- 각 hook 안 guard: 있음 ✅
- 정상 · rule 로 재발 방지

## 금지

1. `~/.claude/settings.json` 에 프로젝트 hook 등록 X
2. hook script 안 guard 생략 X
3. 하드코딩된 프로젝트 경로 X (`$CLAUDE_PROJECT_DIR` 사용)
4. 전역 설정에 프로젝트 관련 로직 X

## 관련

- `.claude/rules/best-practices.md` § Template kit 원칙
- `.claude/rules/plugin-structure.md` (플러그인 구조)
- `.claude/rules/direction-first.md` § 4갈래 대상 (kit·설정·target·글로벌)
- `setup/modules/03-settings.bat` (전역 배포 스크립트)
- `.claude/scripts/verify-hook-scope.py` (검증 · 예정)
