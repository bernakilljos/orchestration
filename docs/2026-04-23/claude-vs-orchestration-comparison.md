# Claude 방향 vs orchestration_v1 방향 비교

> 작성: 2026-04-23
> 근거 자료: `docs/screens/arch/claude-*.{jpg,png}` (Ruben Hassid + Brij Pandey 다이어그램 4장)

## 1. 분석 대상

| 다이어그램 | 출처 | 핵심 메시지 |
|-----------|------|------------|
| `claude-mindmap-eating-everything-hassid.png` | Ruben Hassid | Claude = 챗봇이 아니라 OS 레이어 (6대 영역) |
| `claude-code-architecture-reference-pandey.jpg` | Brij Pandey | Claude Code = 7층 케이크 (Memory→Skills→MCP→Commands→Agents→Workflows) |
| `claude-code-project-structure-pandey.jpg` | Brij Pandey | Claude Code 프로젝트 구조 치트시트 |
| `claude-md-design-guide-pandey.jpg` | Brij Pandey | CLAUDE.md = AI 팀원의 온보딩 문서 |

## 2. 같은 방향 (이미 우리 킷에 내장)

| Claude 방향 | 우리 위치 |
|-------------|----------|
| CLAUDE.md = AI 에이전트 메모리/온보딩 | `./CLAUDE.md` ✓ |
| Skills (auto-activate) | `plugins/*/skills/`, `.claude/skills/` ✓ |
| MCP = USB-C for AI | `plugins/mcp_*` 8개 ✓ |
| Hooks (lifecycle) | `.claude/hooks/`, `plugins/*/hooks/` ✓ |
| Slash Commands | `.claude/commands/` 170+ ✓ |
| Multi-Agent / Sub-agent | codex/gemini/claude-auto 워커 ✓ |
| Scope: Folder > Project > Global | `CLAUDE.md § 6` 일치 ✓ |
| WHAT/WHY/HOW 프레임워크 | `CLAUDE.md § 1~3` 일치 ✓ |
| 500줄 이하 유지 | `CLAUDE.md § 5` 일치 ✓ |
| `.claudeignore` 패턴 | `.gitignore` + 자체 무시 규칙 ✓ |

## 3. 차이점 (우리만의 방향)

| 영역 | Claude 방향 | **orchestration_v1 방향** |
|------|-------------|--------------------------|
| **AI 모델** | Claude 단일 (Opus/Sonnet/Haiku) 깊이 강화 | Claude+Codex+Gemini **멀티AI 라우팅** (비용·속도·품질 최적화) |
| **에이전트 모델** | 한 세션 내 sub-agent (Layer 5) | **외부 워커 프로세스** (codex-auto.bat ×4, gemini-auto.bat ×2) |
| **태스크 핸드오프** | Conversation + AskUserQuestion + Artifacts | **파일 기반** (`.claude/tasks/task-*.md` SoT) |
| **플러그인 모델** | Skills/Hooks 직접 (`~/.claude/skills/`) | **`plugins/` SoT → sync → `.claude/`** (드리프트 방지) |
| **언어** | English-default | **Korean-default UX** |
| **로컬 백업** | Cloud-API 기본 | **`exec_offline` Ollama 폴백** (cost-zero 모드) |
| **품질 게이트** | 없음 (개인 취향) | **금지 8개 명시** (`?.` chaining, 하드코딩 등) |
| **상태 관리** | 인메모리 (세션) | **`.claude/state/` 영속화** (heartbeat, quota, token-log) |

## 4. 갭 (Claude에 있지만 우리에 약했던 부분 → exec_claude 로 보완)

| Claude 기능 | 보완 전 상태 | 보완 (`exec_claude`) | 우선순위 |
|-------------|-------------|----------------------|---------|
| AskUserQuestion | 일반 텍스트로만 묻기 | `/claude-ask` + `skill-claude-ask` | 중 |
| Extended Thinking 컨트롤 | 없음 | `/claude-thinking` + `skill-claude-thinking` | 저 |
| Artifacts (인터랙티브) | 정적 PDF/PPT 만 | `/claude-artifact` + `skill-claude-artifact` | 고 |
| Connectors (1-click 인증) | `mcp_collab` 수동 | `/claude-connectors` (추천·검색·등록) | 중 |
| Claude in Excel/Chrome | MCP 경유 | (Anthropic 영역 — 보완 안 함) | 저 |

## 5. 핵심 결론

**우리 프로젝트는 Claude 방향의 80%를 내장하면서, 20%를 "외부 오케스트레이션" 관점으로 확장**:
- Claude 그림 = **한 AI 를 깊게 쓰는 법**
- orchestration_v1 = **여러 AI 를 비용 최적화하며 협업시키는 법**

## 6. 두 플러그인의 역할 분담 (보완 후)

```
┌──────────────────────────────────────────┐
│  exec_orch  — 멀티AI 협업 라우팅          │
│  ─────────────────────────                │
│  · Codex (코드 500줄+)                    │
│  · Gemini (검증·문서)                     │
│  · Claude-auto (병렬 보조)                │
│  · 파일 기반 task 핸드오프                │
│  · 워커 프로세스 격리                     │
└──────────────────────────────────────────┘
                  +
┌──────────────────────────────────────────┐
│  exec_claude — Claude 깊이 활용 (NEW)     │
│  ─────────────────────────                │
│  · /claude-ask       (구조화 질문)        │
│  · /claude-artifact  (인터랙티브 HTML)    │
│  · /claude-connectors (SaaS 통합)         │
│  · /claude-thinking  (Extended Thinking)  │
│  · /claude-status    (가용성 점검)        │
└──────────────────────────────────────────┘

→ orch 는 "어떤 AI 가 할까", claude 는 "Claude 가 어떻게 잘 할까"
```

## 7. 보완 후 자산 가치

| 자산 | 보완 전 | 보완 후 |
|------|---------|---------|
| 외부 워커 모델 | 강 | 강 |
| 파일 기반 핸드오프 | 강 | 강 |
| plugins/ SoT 패턴 | 강 | 강 |
| Claude 깊이 활용 | **약** | **중-강** |
| 인터랙티브 산출물 | **없음** | **있음 (HTML)** |
| 구조화 사용자 입력 | **없음** | **있음 (claude-ask)** |

## 8. 다음 단계

1.  `plugins/exec_claude/` 생성 완료
2. ⏳ sync-plugins → `.claude/` 반영
3. ⏳ `guide.txt § exec_claude` 섹션 추가
4. ⏳ setup 모듈에 추가 (자동 설치)
5. ⏳ 시연 PPT 3종 생성 (Claude Code 설명·사용 단계·플러그인 사용법)
6. ⏳ git push

## 9. 참조

- `plugins/exec_claude/README.md` — 플러그인 설명
- `plugins/exec_claude/SPEC.md` — 스펙
- `docs/screens/arch/` — 분석 원본 11장
- `CLAUDE.md` — 본 프로젝트 규칙
