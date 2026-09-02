# 대상 확정 우선 룰 (Direction-First)

> **근거**: 2026-08-12 세션 — 헌장 통합 지시받고 orchestration_v1 kit 자체를 감사한 삽질. 사용자는 setup/templates 또는 install target 을 원했음.
> **이유**: 대상 안 잡고 시작 = 방향 오해 → 사용자 재지시 → 짜증. 매 세션 반복.

## 절대 룰

**사용자 작업·감사·수정 지시 시 첫 응답 첫 줄에 대상 명시 → 유지·정정 확인 → 실행.** 대상 확정 전 grep·Read·Edit·Bash 착수 X.

## 대상 4갈래 (자동 후보 나열)

> **경로 표기**: `<KIT_ROOT>` = 이 kit 이 설치된 폴더 (환경마다 다름 — Windows 예: `C:\pjt\orchestration_v1\`, Linux 예: `~/orchestration_v1/`, Mac 예: `~/dev/orchestration_v1/`). 하드코딩 X — 룰은 컴퓨터·사용자 무관하게 적용.

| # | 경로 | 언제 · 감지 방법 |
|---|---|---|
| 1 | `<KIT_ROOT>` | kit 자체 감사·리팩터·룰 정리·hook 축약. **감지**: `.claude-plugin/plugin.json` + `plugins/exec_orch/` 동시 존재 |
| 2 | `<KIT_ROOT>/setup/templates/` (+ `setup/modules/`) | install 배포용 template·글로벌 CLAUDE.md 등. **감지**: basename=`templates` + parent=`setup` |
| 3 | install 대상 실운영 프로젝트 (경로 사용자 지정 필요) | "실운영"·"하드코딩 실측"·"재발 방지 헌장"·비즈니스 로직. **감지**: `CLAUDE.md` 또는 `.claude/` 있으나 kit marker 없음 |
| 4 | `~/.claude/` (또는 `%USERPROFILE%\.claude\`) | "글로벌"·"settings"·"모든 프로젝트 공통". **감지**: HOME·USERPROFILE 환경변수 아래 `.claude` |

## 첫 응답 형식 (고정)

```text
대상: <path> (kit/설정/target/글로벌) — 맞으면 진행, 아니면 정정.
```

여러 경로 걸치면:
```text
대상: <path1> + <path2> — 둘 다 손대야 함 (설정 배포 + kit 원본)
```

## 자동 판정 힌트

| 사용자 어휘 | 후보 |
|---|---|
| "install a/b"·"배포"·"공통 kit"·"template" | 2 (setup/templates) |
| "실운영"·"하드코딩 실측"·"재발 방지 헌장"·비즈니스 지표명 (bar_tone·KPI 등) | 3 (경로 물어봄) |
| "kit 자체"·"룰 21개"·"hook 40개"·"플러그인" | 1 (orchestration_v1) |
| "settings"·"글로벌"·"~/.claude" | 4 |
| 특정 프로젝트명 (RMS·ICM·IFRS 등) | 3 그 프로젝트 폴더 |

## 대상 X 상태에서 실행하면 = 위반

- grep·Read·Edit·Bash 어떤 도구든 대상 확정 전 착수 = 룰 위반
- "일단 kit 뒤져보자" = 위반
- 후보 나열도 X 하고 진행 = 위반

## 예외 (첫 응답 대상 명시 생략 허용)

- 순수 질문 (설명·yes/no·설계 토론)
- 이미 이번 세션에서 대상 명시했고 사용자가 대상 안 바꿈
- 사용자가 대상 경로를 첫 문장에 명시함

## 강제 (5중 박기)

1. 이 룰 파일
2. memory `feedback_confirm_target_first.md`
3. CLAUDE.md § 3.0 (0순위 지침 최상단)
4. `.claude/hooks/user-prompt-auto-planner.sh` — 매 트리거 시 systemMessage 로 대상 확정 요청 주입 (10번째 X, 매번 O)
5. `.claude/hooks/periodic-rules-reminder.sh` 리스트 첫 줄

## 참조

- `.claude/rules/failure-mode.md` § 전수조사 위반
- `.claude/rules/best-practices.md` § Template kit 원칙
- `feedback_template_kit_principle.md`
- `feedback_confirm_target_first.md`
