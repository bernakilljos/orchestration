---
description: "주제 보고 자동 판단 — 마인드맵·레이어·치트시트 중 가장 적합한 형식 선택해 생성"
allowed-tools: Bash(where:*), Bash(claude mcp list:*), Write, Bash(python:*)
---

## Context
- 사용 가능 패턴:
  - mindmap (방사형) — `arch-mindmap`
  - layered (레이어 케이크) — `arch-layered`
  - cheatsheet (3컬럼) — `arch-cheatsheet`

## Your task

주제: `$ARGUMENTS`

---

### Step 1 — 패턴 자동 판단 (Claude 추론)

주제 성격 분석 후 결정:

| 신호 | 선택 |
|------|------|
| 여러 독립된 영역을 한 번에 보여줘야 함 (제품·플랫폼 전체뷰) | **mindmap** |
| 위→아래 순서·계층·의존이 의미 있음 (스택·OSI·빌드 단계) | **layered** |
| 정보 밀도 ↑ + 빠른 스캔용 (프로젝트 구조·명령어·API 레퍼런스) | **cheatsheet** |

판단 로그 출력:
```
🎯 주제: <topic>
🔍 분석:
  - 독립 영역 vs 계층: <판단>
  - 정보 밀도: <낮음/높음>
  - 사용 시나리오: <발표/온보딩/레퍼런스>
✅ 선택: <pattern>
   이유: <한 문장>
```

### Step 2 — 선택된 패턴 위임

해당 커맨드 본문 그대로 실행 (skill 활성화 + 렌더 + 출력):
- mindmap → `skill-arch-mindmap` + Mermaid 렌더
- layered → `skill-arch-layered` + python-pptx/ReportLab
- cheatsheet → `skill-arch-cheatsheet` + HTML+wkhtmltopdf

> 사용자가 명시적 패턴 키워드(`마인드맵으로`, `레이어로`, `치트시트로`)를 함께 말했으면 그것을 우선.

### Step 3 — 결과 보고

```
✅ 자동 선택 결과
- 패턴: <name>
- 이유: <one-liner>
- 산출물: outputs/arch/<pattern>-<slug>-<date>.<ext>

다른 형식으로 보고 싶으시면:
  /arch-mindmap <topic>
  /arch-layered <topic>
  /arch-cheatsheet <topic>
```
