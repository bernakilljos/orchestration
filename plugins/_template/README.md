# _template — 플러그인 이름

> **한 줄 설명**: 뭘 하는 플러그인인지 간결히 (plugin.json.display 와 동일)
> **Prefix**: `template_`  | **버전**: 0.1 | **Status**: spec-only

---

## 📖 개요

- 이 플러그인이 **왜** 존재하는가 (문제 제기)
- **무엇**을 자동화하는가 (기능 요약)
- **언제** 사용하는가 (트리거·상황)

---

## 🚀 빠른 시작

```bash
# 설치 (install 후 자동 sync)
bash .claude/scripts/sync-plugins.sh

# 기본 실행
/<default-command>
```

---

## 📋 커맨드

| 커맨드 | 설명 | 예시 |
|---|---|---|
| `/<cmd-1>` | 설명 | `/<cmd-1> --option value` |
| `/<cmd-2>` | 설명 | `/<cmd-2> target.md` |

---

## 🧠 스킬

| 스킬 | 역할 |
|---|---|
| `skill-xx-yyy` | 언제 자동 활성화되는지 |

---

## 🤖 에이전트

| 에이전트 | 역할 |
|---|---|
| `agent-xx-yyy` | 담당 |

---

## 🪝 훅

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `hook-xx-yyy` | PreToolUse/PostToolUse/Stop/... | 언제 어떤 검증·처리 |

---

## 🔗 의존성

- **플러그인**: `exec_orch` (코어)
- **MCP**: 해당 없음 또는 필요한 MCP 서버
- **환경변수**: `FOO_API_KEY`, `BAR_TOKEN`

---

## 💡 사용 예시

### 예시 1: 기본 사용
```
사용자: "이걸 해줘"
Claude: /<cmd-1> 실행 → 결과
```

### 예시 2: 고급 옵션
```
/<cmd-2> --mode advanced --output data/
```

---

## 🧪 테스트

```bash
bash plugins/_template/tests/run.sh
```

---

## 📝 변경 이력

- 0.1 (2026-04-19) — 초기 스펙
