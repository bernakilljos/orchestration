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

## Git Bash 에서 등록하면 `/c` 가 `C:/` 로 바뀐다 (2026-09-09 · 실사고)

`cmd /c npx ...` 를 **Git Bash 에서** `claude mcp add` 로 등록하면 MSYS 경로 자동변환이
`/c` 를 `C:/` 로 바꿔 버린다. 저장된 결과:

```json
{ "command": "cmd", "args": ["C:/", "npx", "-y", "@playwright/mcp"] }   // 망가진 것
{ "command": "cmd", "args": ["/c",  "npx", "-y", "@playwright/mcp"] }   // 올바른 것
```

`/c` 가 없으니 cmd 가 **대화형 셸로 떠서** MCP 프로토콜을 말하지 않고 30초 타임아웃난다.
증상은 "connection timed out" 이라 콜드스타트로 오해하기 쉽다 — 실제로 그 패키지를
직접 `npx -y <pkg>` 로 띄우면 **3~5초에 정상 응답**한다. 그 대조가 판별법이다.

2026-09-09 에 이것으로 **4개 서버(fetch·playwright·sequential-thinking·context7)가
전부 죽어 있었다.**

### 처방
1. 등록은 **PowerShell 에서** 한다 (MSYS 변환 없음):
   `claude mcp add <name> -s user -- cmd /c npx -y <pkg>`
   Git Bash 에서 해야 하면 `MSYS_NO_PATHCONV=1` 을 앞에 붙인다.
2. 등록 후 **저장된 args 를 눈으로 확인**한다 — `args[0]` 이 `/c` 인지.
   `claude mcp list` 는 명령줄을 그대로 찍어 주므로 여기서 바로 보인다.
3. 같은 서버가 두 스코프에 등록되면 `claude mcp list` 가 `[Conflicting scopes]` 로 알려 준다.
   OAuth 토큰은 엔드포인트별로 저장되니 하나만 남긴다.

## npm 에 없는 패키지가 설정에 들어가 있었다 (2026-09-09)

`@modelcontextprotocol/server-fetch` = **E404**. `mcp-server-fetch`(npm) 은
`0.0.1-security` = 자리만 잡아둔 플레이스홀더라 이것도 아니다.
공식 fetch 서버는 **파이썬**이다 — `uvx mcp-server-fetch` (mcp-fetch 1.30.0, 6초 응답).

이 룰의 `npm view` 검증 의무는 **이미 등록된 설정에도** 적용해야 한다. 새로 넣을 때만
검증하고 기존 것은 안 봤더니, 존재하지 않는 패키지가 계속 30초씩 타임아웃을 내고 있었다.

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
