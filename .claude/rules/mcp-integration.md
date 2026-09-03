# MCP 통합 룰 (Headroom + claude-mem + task-observer)

> **근거**: 2026-09-02 사용자 요청 · 오픈소스 MCP 5종 검토 후 3개 (Headroom, claude-mem, task-observer) 채택. OmniRoute 는 라우팅이 우리 route.py 정면 겹침으로 제외 (사용자 결정). claude-code-setup 은 특정 도구 아닌 통칭.
> **이유**: 우리 kit 이 라우팅·룰·도메인 특화 우세 · 압축·자동 세션 관측·태스크 패턴 캡처는 오픈소스 세계급 · 결합이 최적. **모두 무료 (Apache 2.0 / 로컬 오픈소스).**

## 절대 룰

**Headroom = 프롬프트 압축 프록시 (60~95% 절감). claude-mem = 자동 세션 관측·복원 (SQLite + Chroma). 우리 route.py·memory 시스템·rule 은 유지·병행.**

## 역할 분리 매트릭스

| 축 | 우리 kit | Headroom | claude-mem |
|---|---|---|---|
| **라우팅·budget·quota** |  `route.py` · `orca.db` |  |  |
| **감사·규제·한국어 룰** |  `.claude/rules/*` · CLAUDE.md § 7 |  |  |
| **컨텍스트 압축 (AST)** |  |  `headroom_compress`·`retrieve`·`stats` |  |
| **prompt 캐시 (Anthropic)** |  `lib/prompt_cache.py` | 병행 (프록시 앞단) |  |
| **명시 memory (도메인 자산)** |  `~/.claude/projects/<proj>/memory/*.md` · MEMORY.md 인덱스 |  |  |
| **자동 세션 관측·복원** | 부분 (`activations`·`decisions` 테이블) |  |  SessionStart / UserPromptSubmit / PostToolUse / Stop / SessionEnd hook |
| **벡터 검색** |  (TF fallback) |  |  Chroma |
| **크로스 디바이스 memory 동기화** |  |   (cmem.ai Pro 옵션 · 현재 OFF) |

## Headroom 통합

- **설치**: `pip install "headroom-ai[all]"` (`headroom` CLI)
- **MCP 등록**: `headroom mcp install` (Claude Code + Codex 자동)
- **프록시 서버**: `headroom proxy` (127.0.0.1:8787)
- **env 세팅**: `ANTHROPIC_BASE_URL=http://127.0.0.1:8787`
- **MCP 도구**: `headroom_compress`·`headroom_retrieve`·`headroom_stats`
- **재시작**: proxy 종료 시 재시작 필요 · autostart hook 로 해결

### Headroom 자동 시작 hook
- `.claude/scripts/mcp-autostart.sh` 가 SessionStart 시 실행
- 이미 돌면 skip · 없으면 백그라운드 spawn (`nohup headroom proxy &`)
- 로그: `.claude/logs/headroom-proxy.log`

## claude-mem 통합

- **설치**: `npx -y claude-mem install --provider claude`
- **plugin dir**: `%USERPROFILE%\.claude\plugins\marketplaces\thedotmack`
- **저장소**: `~/.claude-mem` (SQLite + Chroma)
- **Worker port**: `127.0.0.1:37777` (설정 가능 · `CLAUDE_MEM_WORKER_PORT`)
- **Cloud sync**: **OFF** (local only · cmem.ai Pro 는 별도 검토)
- **Auto-memory**: native Claude Code memory 유지 (병행)
- **5 hook 자동 등록**: SessionStart · UserPromptSubmit · PostToolUse · Stop · SessionEnd

### claude-mem worker 자동 시작
- `.claude/scripts/mcp-autostart.sh` 가 SessionStart 시 실행
- `npx claude-mem start` 백그라운드
- 이미 돌면 skip · 헬스체크: `curl http://127.0.0.1:37777/api/health`

### Memory injection
- 2번째 세션부터 이전 세션 컨텍스트 자동 주입
- 우리 명시 memory (`MEMORY.md` 인덱스) 와 병행 · 서로 다른 축

## task-observer 통합 (Skill)

- **설치**: `npx -y skills add rebelytics/one-skill-to-rule-them-all --skill task-observer --agent claude-code`
- **정체**: MCP 서버가 아니라 **Claude Code Skill** (`.claude/skills/task-observer/`)
- **역할**: 태스크 실행 관측 · 패턴·사용자 수정·워크플로 인사이트·재사용 가능 스킬 캡처
- **활성**: multi-step 태스크·agentic workflow·post-task 피드백·"One Skill to Rule Them All" 트리거 시 자동 활성 (description matching)
- **저장**: skill 자체 observation log (`references/observation-log.md`)
- **라이선스**: 오픈소스 · 로컬 (외부 전송 X)
- **Security**: Gen Med Risk · Socket 0 alerts · Snyk Low Risk
- **주의**: skill 은 full agent permissions 로 실행 · SKILL.md·scripts 검토 후 신뢰

### task-observer 와 우리 kit 관측 시스템 병행
- 우리 `orca.db.activations`·`decisions`·`determinism` = **kit 도메인 관측** (감사·워커·룰 적용)
- task-observer = **skill 개선 기회 관측** (사용자 수정 패턴·방법론·재사용 가능성)
- 서로 다른 축 · 병행

## 우리 memory vs claude-mem — 병행 원칙

| 종류 | 언제 |
|---|---|
| **우리 명시 memory** (`~/.claude/projects/<proj>/memory/*.md`) | **도메인 자산** — feedback·project·reference·user. 사용자 명시·중요·장기 보존. Write tool 로 등재. |
| **claude-mem 자동 관측** (Observation) | **세션 관측 · 자동 캡처** — 결정·수정·데드엔드·서프라이즈. 자동 · 압축 · 벡터 검색용. |

**금지**: claude-mem 자동 캡처만 믿고 명시 memory 안 등재. 둘 다 병행.

## 우리 hook 과 충돌 방지

우리 kit SessionStart hook 17개 이미 등록. claude-mem 은 자기 SessionStart hook 자동 추가 (plugin marketplace 방식).

### 순서
1. 우리 kit 기존 hook (17개) — 그대로 유지
2. `.claude/scripts/mcp-autostart.sh` — 마지막에 추가 (Headroom proxy + claude-mem worker 시작)
3. claude-mem 자체 hook — plugin marketplace 관리 (자동)

### 충돌 없음 확인
- 우리 hook = kit 도메인 (룰·감사·watchdog·정리)
- claude-mem hook = 컨텍스트 자동 관측 (독립 SQLite `~/.claude-mem`)
- 저장소 분리 · 포트 분리 · 로그 분리

## 재시작·유지·헬스체크

| 서비스 | 헬스체크 | 재시작 |
|---|---|---|
| Headroom proxy | `curl http://127.0.0.1:8787/health` (실측 필요) | `headroom proxy` 재실행 |
| claude-mem worker | `curl http://127.0.0.1:37777/api/health` | `npx claude-mem restart` |

- `.claude/hooks/check-mcp-health.sh` 확장: 위 2개 헬스체크 추가 (Phase 4 후속)
- 죽으면 SessionStart 다음 세션에서 mcp-autostart.sh 가 자동 재기동

## 상용·라이선스

| 도구 | 라이선스 | 상용 가능? |
|---|---|---|
| Headroom | **Apache 2.0** (10k+ ) |  |
| claude-mem | 오픈소스 |  (Cloud sync 는 별도) |

## 금지

1. 우리 `route.py`·`orca.db` 를 Headroom/claude-mem 로 대체 X (기능·도메인 다름)
2. claude-mem cloud sync 임의 활성 X (개인정보·시크릿 유출 위험 · 사용자 명시 시만)
3. Headroom proxy 없이 `ANTHROPIC_BASE_URL` 만 세팅 X (연결 실패)
4. claude-mem worker 다중 인스턴스 X (포트 충돌)
5. 명시 memory 안 등재하고 자동 관측만 의존 X (도메인 자산 유실)

## install 순서 (룰 준수)

kit 편집 (이 파일 · autostart 스크립트 · CLAUDE.md § 3.6) → git commit → `sync-plugins.sh` → target 배포 (setup/modules 갱신).

## 관련

- `.claude/scripts/mcp-autostart.sh` (자동 시작 스크립트)
- `CLAUDE.md § 3.6 MCP 설치 규칙` (표기 추가)
- `~/.claude/projects/C--pjt-orchestration-v1/memory/reference_headroom_claude_mem.md` (memory 등재)
- `.claude/rules/mcp-install-rules.md` (기존 규칙 · 정합)
- Headroom GitHub: github.com/headroomlabs-ai/headroom
- claude-mem GitHub: github.com/thedotmack/claude-mem
