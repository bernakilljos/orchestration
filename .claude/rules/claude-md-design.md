# CLAUDE.md 설계 규칙

> **출처**: Brij Kishore Pandey — "How to Design a CLAUDE.md That Actually Works"
> **적용**: 프로젝트 루트 `CLAUDE.md` + 하위 폴더 국소 CLAUDE.md

## 3 Scopes (Last wins on conflicts)

| Scope | 경로 | 용도 |
|---|---|---|
| **Global** | `~/.claude/CLAUDE.md` | 모든 프로젝트 공통 (코딩 스타일·개인 선호) |
| **Project** | `./CLAUDE.md` | 이 프로젝트 규칙 (build·test·team 컨벤션) |
| **Folder** | `./src/CLAUDE.md` 등 | 모듈 국소 규칙 (API·컴포넌트·utils) |

**충돌 해결**: Folder → Project → Global 순서로 가까운 것이 이긴다.

## WHAT / WHY / HOW 프레임

### WHAT (Context 제공)
- 프로젝트 이름·목적
- 기술 스택·버전
- 저장소 구조 맵
- 핵심 의존성
- 환경 변수

### WHY (원칙 세팅)
- 아키텍처 결정
- 코드 스타일·lint 규칙
- 네이밍 컨벤션
- 안티패턴 회피 (하지 말아야 할 것)
- 에러 처리 접근

### HOW (워크플로우 정의)
- **Build**: `npm run build`
- **Test**: `npm test`
- **Lint**: `eslint . --fix`
- **Commit** 포맷
- **Deploy** & CI/CD 단계

## 5 Rules

1. **`/init` 먼저** — Claude 가 초기 스캐폴드 잡게 한 후 큐레이션
2. **500줄 이하 유지** — 너무 길면 무시됨. 참조 파일로 분산
3. **Hooks 로 100% 강제** — 메모리·프롬프트는 7~80% 지켜짐. Hooks 는 절대적
4. **월간 업데이트** — 살아있는 문서. 아키텍처 변화 반영
5. **참조 중심, 중복 금지** — `package.json`, `tsconfig` 같은 파일은 가리키기만

## BE SPECIFIC — VAGUE vs PRECISE

|  Vague |  Precise |
|---------|-----------|
| "Write clean code" | "Use camelCase for variables, PascalCase for components" |
| "Test everything" | "npm test --watch, min 80% coverage for utils/" |

## 이 프로젝트 적용 상태

-  Project CLAUDE.md — 이 규칙으로 재구성 (2026-04-19)
-  WHAT/WHY/HOW 프레임 적용
-  500줄 이하 (현재 ~170줄)
-  Hooks 사용 (`.claude/settings.json` hooks)
-  참조 중심 (`guide.txt`·`docs/architecture-patterns.md`·`.claude/rules/*`)

## 참조

- `CLAUDE.md` (프로젝트 루트)
- `docs/architecture-patterns.md` § 전체 설계 원칙
- `docs/upgrade-analysis-2026-04-19.md` § 이미지 4 (Brij 설계 가이드)
