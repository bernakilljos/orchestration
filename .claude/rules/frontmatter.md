# Frontmatter 표준

> **적용 범위**: `plugin.json`, 커맨드 `.md`, 스킬 `.md`
> **스키마**: `.claude-plugin/plugin-schema.json`

## plugin.json (v1.2)

### 필수 7 필드

```json
{
  "name":     "<prefix>_<feature>",
  "display":  "한 줄 한글 설명 (이름 반복 없이)",
  "prefix":   "<prefix>_",
  "version":  "1.0",
  "status":   "stable | experimental | spec-only | deprecated",
  "phase":    0,
  "commands": "commands/"
}
```

### 권장 추가 필드

```json
{
  "skills":   "skills/",
  "agents":   "agents/",
  "hooks":    "hooks/",
  "dependencies": {
    "plugins": ["exec_orch"],
    "mcp":     [],
    "env":     ["API_KEY_NAME"]
  },
  "entry_points": {
    "default_command": "check",
    "core_skills":     ["skill-xx-yyy"]
  },
  "metadata": {
    "category":       "문자열",
    "tags":           ["tag1"],
    "author":         "이름",
    "created":        "YYYY-MM-DD",
    "updated":        "YYYY-MM-DD",
    "precedence":     0,
    "token_estimate": 5000
  }
}
```

## 커맨드 `.md` frontmatter

```yaml
---
description: "한 줄 한글 설명 (이름 반복 없이 — 플러그인 이름 금지)"
allowed-tools: Bash(cmd:*), Read, Edit
---
```

- `description` 은 한글. 왼쪽 커맨드명과 중복 금지.
- `allowed-tools` 는 필요한 것만 최소로.

## 검증

```bash
python .claude/scripts/validate-plugin-schema.py          # 전체
python .claude/scripts/validate-plugin-schema.py <name>   # 단일
python .claude/scripts/validate-plugin-schema.py --strict # warning 도 실패
```

## 금지 사항

- description 에 플러그인 이름 반복 (`review_qa — 코드 리뷰...` )
- optional chaining 스타일 표기
- 한글·영문 혼용 (description 은 한글로 통일)
- version 패턴 위반 (`1` , `1.0` )
