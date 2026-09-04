# MCP 설치 룰

> **근거**: CLAUDE.md § 7-9 (`거짓 npm 패키지명 커맨드 (실측 없이) — npm view 검증 필수`).
> **이유**: hallucinated npm package 명령은 사용자 머신에서 404 → 신뢰 추락.

## 절대 룰

**npm package 명령을 .md / .json / 커맨드에 작성 전 `npm view <package>` 로 실재 확인.**

## 검증 절차 (의무)

```bash
# 1. 실재 확인
npm view @scope/package version
# Output 있음 → 실재
# Output 없음 (E404) → fabrication 의심 → 다른 후보 검색

# 2. 명령에 적용
# Windows: cmd /c npx <package> ... (shell 교차호환)
# Unix: npx <package> ...
```

## Windows npx 래퍼 의무

bash → npx 직접 호출 시 PATH 문제. **`cmd /c npx` 래퍼 사용**.

```json
// .claude/settings.json mcp 등록 (잘못된 예 )
{
  "mcp": {
    "my-server": {
      "command": "npx",
      "args": ["@scope/server"]
    }
  }
}

// 올바른 예 
{
  "mcp": {
    "my-server": {
      "command": "cmd",
      "args": ["/c", "npx", "@scope/server"]
    }
  }
}
```

## OAuth / 인증 도구

| 항목 | 어디 | 어떻게 |
|---|---|---|
| 실제 키 / 토큰 | `.env` 또는 OS 환경변수 | `.env` 는 gitignore |
| 변수 이름 | `.env.example` + plug `README.md` | `MCP_FOO_TOKEN=` placeholder |
| 개발자 콘솔 URL | plug `README.md` | "토큰 발급: https://..." |

**절대 commit 금지**: `.env`, raw token, key 파일.

## plug_<category> 공통 준수

| 카테고리 | 준수 사항 |
|---|---|
| `plug_design` (Figma·Canva·Gamma) | npm view 검증·npx 래퍼·env 변수 |
| `plug_dev` (GitHub·Sentry·Codex) | npm view 검증·OAuth env |
| `plug_data` (Notion·Linear·Airtable) | API key env |
| `plug_web` (Playwright·Puppeteer) | npm view 검증·browser path 자동 검색 |
| `plug_collab` (Slack·Discord) | webhook env·OAuth env |
| `plug_docs` (Notion·Confluence) | API key env |
| `plug_media` (YouTube·Spotify) | API key env |

## 자동 검증

```bash
# 모든 MCP 명령 grep + npm view
bash .claude/scripts/validate-mcp-commands.sh

# 결과:
# OK:   @anthropic-ai/mcp-server-...
# FAIL: @fake/package — E404 (fabrication 의심)
```

## 흔한 fabrication 안티패턴

| 잘못된 명령 | 왜 | 올바른 행동 |
|---|---|---|
| `npx @anthropic/figma-mcp` (가짜) | 실재 X | npm view → 정확한 이름 (`figma-developer-mcp`) |
| `npx @claude/mcp-notion` (가짜) | scope 추측 | 공식 docs 확인 |
| `npm install -g <package>` | 시스템 의존 | `npx` 또는 local install |
| `pip install <pkg>` 권한 | 시스템 권한 | venv 또는 `pip install --user` |

## 호환성 (cross-machine)

- 절대 경로 X — `npx` 동적 검색
- Windows / macOS / Linux 모두 동작 (`cmd /c` 래퍼)
- node 버전 의존 X 권장 (`engines` 명시)

## 참조

- `CLAUDE.md § 3.6 MCP 설치 규칙` (절차)
- `CLAUDE.md § 7-9` (금지)
- `guide.txt § 8` (상세)
- `docs/upgrade-notes-2026-04-23.md` (npm view 사례)
- `.claude/rules/best-practices.md` § 시크릿 관리
- `.claude/rules/failure-mode.md` § fabrication 방지
