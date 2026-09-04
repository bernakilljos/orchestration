# 파일 명명 규칙

## 플러그인 디렉토리
- `plugins/<prefix>_<feature>/` — 소문자·언더스코어
- prefix 등록 위치: `.claude-plugin/plugin.json` § `prefix_convention`
- 템플릿 제외: `plugins/_template/` (언더스코어 시작으로 구분)

## 커맨드
- `plugins/<plugin>/commands/<name>.md`
- `<name>` 은 kebab-case 허용 (`yt-upload.md`)
- 충돌 시 sync-plugins.sh `RENAME_MAP` 에 접두사 부여 규칙 등록
  - 예: `mcp_dev/commands/install.md` → `.claude/commands/mcp_dev-install.md`

## 스킬
두 가지 네이밍 혼재 (점진 통일):
- 번호형 (레거시): `skill-XX-<topic>.md` (skill-01 ~ skill-38)
- 의미형 (권장): `<feature>-<purpose>.md` — kebab-case 우선, underscore 호환 허용 (예: `route_dispatch.md` legacy / `auto-planner.md` 권장)

## 훅
- 스펙: `hooks/hook-XX-<event>.md`
- 스크립트: `hooks/<이름>.sh` (md 와 같은 prefix)

## 에이전트
- `agents/agent-XX-<role>.md`
- **예외**: `plugins/vendor_*/agents/` 는 외부 표준 파일명 보존 (kebab-case 그대로) — vendoring 호환성 (예: `vendor_voltagent/agents/data-scientist.md`). plugin.json 의 `metadata.vendored: true` 명시 필수.

## 문서
- 일반 문서: `docs/YYYY-MM-DD/<topic>.md`
- 영구 문서: `docs/<permanent-name>.md` (예: `docs/architecture-patterns.md`)
- 한글 파일명 허용 — 의미 명확하면 우선 선택 (예: `로드맵.md`)

## 스크립트
- bash: `.claude/scripts/<name>.sh`
- python: `.claude/scripts/<name>.py`
- Windows bat: `setup/modules/NN-<name>.bat`

## 금지

- 공백 포함 파일명 (`my file.md` )
- 대문자 시작 (`MyPlugin.md`  — 대문자 사용은 CLAUDE.md 같은 전통적 규약만)
- `.backup`, `.bak`, `.orig` 확장자 — cleanup-orphans 훅이 자동 제거
