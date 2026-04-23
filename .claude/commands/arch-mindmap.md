---
description: "방사형 마인드맵 다이어그램 1장 생성 — 중앙 주제 + 카테고리 + 노드"
allowed-tools: Bash(where:*), Bash(claude mcp list:*), Write, Bash(python:*), Bash(npx:*)
---

## Context
- Mermaid MCP: !`claude mcp list 2>/dev/null | grep -i mermaid && echo OK || echo 없음`
- Canva MCP:   !`claude mcp list 2>/dev/null | grep -i canva   && echo OK || echo 없음`
- Gamma MCP:   !`claude mcp list 2>/dev/null | grep -i gamma   && echo OK || echo 없음`
- python-pptx: !`python -c "import pptx" 2>/dev/null && echo OK || echo 없음`

## Your task

주제: `$ARGUMENTS`
스타일: Ruben Hassid "Claude is eating up everything" 방사형 마인드맵

---

### Step 1 — 구조 설계 (Claude)

`skill-arch-mindmap` 활성화 후 주제 분석:

```json
{
  "center": "<중심어>",
  "categories": [
    {"name": "<카테고리1>", "nodes": [
      {"title": "<제목>", "desc": "<1~2문장>"}
    ]}
  ]
}
```

규칙:
- 카테고리 4~6개
- 카테고리당 노드 3~5개
- 노드 제목 1~3 단어
- 노드 설명 1~2 문장

`$ARGUMENTS` 가 비어있거나 모호하면 사용자에게 1회 질문 후 진행.

### Step 2 — Mermaid 코드 생성

```mermaid
mindmap
  root(("<center>"))
    <Category1>
      ["<title><br/><desc>"]
    <Category2>
      ["<title><br/><desc>"]
```

저장 경로: `outputs/arch/mindmap-{slug(topic)}-{YYYY-MM-DD}.md`

### Step 3 — 렌더 (가능한 도구 우선순위)

Context 결과에 따라:

1. **Mermaid MCP 있음** → MCP 호출로 PNG 렌더
2. **MCP 없고 npx 있음** → `npx -p @mermaid-js/mermaid-cli mmdc -i {md} -o {png} -t default -b transparent`
3. **둘 다 없음** → `.md` 만 생성하고 GitHub/VSCode preview 안내

추가 옵션:
- **Canva MCP 있음**: 사용자가 "예쁘게" / "디자인 강화" 요청 시 Canva 로 재생성
- **python-pptx 있음**: 사용자가 "PPT 한 장으로" 요청 시 PPTX 생성

### Step 4 — 결과 보고

```
✅ 마인드맵 생성 완료
- 원본: outputs/arch/mindmap-{slug}-{date}.md
- 이미지: outputs/arch/mindmap-{slug}-{date}.png
- 카테고리: N개 / 노드: 총 M개

미리보기:
  중앙: <center>
  └ <Category1>: <node1>, <node2>, ...
  └ <Category2>: ...
```

### 품질 게이트 (출력 전)
- [ ] 카테고리 4~6 범위
- [ ] 노드 텍스트 3줄 이하
- [ ] 균형 (한쪽으로 치우침 없음)
- [ ] 중심어 명확
