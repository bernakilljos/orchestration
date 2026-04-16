# 프로젝트 작업 규칙

## AI 역할 분담

| 작업 유형 | 담당 | 실행 방법 |
|-----------|------|-----------|
| 설계 / 판단 / 승인 | Claude | 직접 처리 |
| 구현 (500줄 이상) | Codex | `codex-a --auto` |
| 구현 (500줄 미만) | Claude | 직접 처리 |
| 검증 / 리뷰 | Gemini | `gemini-a --verify` |

## Claude 행동 규칙

- Claude용 실행 래퍼 만들지 않는다 (`claude-a.bat`, `claude-auto.bat` 등)
  → Claude는 대화에서 직접 구현
- "바로 시작하겠습니다" 후 추가 질문 하지 않는다
  → 정보 확인 먼저, 그 후 시작 선언
- task-instruction.md 작성 후 Codex/Gemini가 자동 처리
  → Claude는 결과 취합 및 최종화

## 인코딩 규칙

- 서버 파일(`.js`/`.ts`/`.java`)에 한글 문자열 직접 쓰지 않는다
  → Codex가 CP949로 저장하면 UTF-8 런타임에서 깨짐
  → 영어 메시지 사용 또는 프론트엔드에서 한글 변환
- 프론트엔드(`.vue`/`.html`)는 UTF-8 저장 → 한글 직접 사용 가능
- `.bat` / `.md` 파일은 install.bat이 자동 변환

## 디자인 규칙

- 화면 참조: `docs/screens/` 폴더에 이미지 저장
- 레이아웃 잠금: AI가 `layouts/` 폴더 수정 금지 (HOOK-07)
- 컴포넌트: `components/` 폴더에는 비즈니스 로직만 추가
- 색상 팔레트: `context/project.md` 정의 준수
- 다크 모드 기본값: Background `#0f1117` / Card `#1e2333` / Border `#2d3550`
- 아이콘: 이모지 또는 인라인 SVG (외부 라이브러리 지양)

## 코드 규칙

- 하드코딩 금지 → 환경변수 또는 설정 파일 참조
  - 경로·포트·도메인·제외패턴 → 변수/설정으로 분리
  - `.bat`: 상단 `set` 변수 선언
  - `.js/.ts`: `config.js` 또는 `.env` 참조
- 기존 변수명 임의 변경 금지
- 주석에 "주인" 단어 사용 금지
- optional chaining (`?.`) 사용 금지

## 파일 수정 규칙

- `task-instruction.md`에 명시된 파일만 수정
- 기존 파일 전체 재작성 금지
- DB / `.sql` 파일 직접 수정 금지 (제안만 가능)
- 동일 파일 동시 수정 금지 (Writer=1)
- 태스크 파일 저장: `.claude/tasks/` 만 (절대경로 금지, 상대경로 사용)

## 배포 규칙

- 운영 배포: `--confirmed` 플래그 필수
- 배포 전 `quality-gate.bat` 통과 필수
- 실패 시 `rollback.bat` 자동 실행

## 알림

- 작업 완료: `notify.bat good`
- 배포 실패: `notify.bat warning`
