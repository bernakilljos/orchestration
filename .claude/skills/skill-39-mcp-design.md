# SKILL-39: MCP 디자인/도구 강제 사용

> PPT, 디자인, 다이어그램, 이메일, 캘린더 등 외부 도구가 필요한 요청 시
> MCP를 우선 사용하고, 없으면 대안을 안내한다.
> 절대 "할 수 없습니다"로 끝내지 않는다.

---

## 트리거 조건

사용자 메시지에 다음 키워드가 포함되면 이 스킬이 자동 활성화된다:

```
PPT, 프레젠테이션, 슬라이드, 발표자료, 발표
디자인, 로고, 배너, 캐릭터, 인포그래픽, 포스터, SNS, 썸네일
다이어그램, 흐름도, 시퀀스, 마인드맵, 아키텍처 도식, ER다이어그램
이메일, 메일, 메일 보내, 메일 확인, 메일 검색
일정, 캘린더, 미팅, 회의, 스케줄
엑셀, 스프레드시트, CSV
워크플로우, 자동화, n8n
Figma, figma.com
```

---

## 실행 절차

### 1단계: MCP 가용성 확인

```
ToolSearch("select:mcp__claude_ai_Gamma__generate") → 스키마 로드 시도
  성공 → MCP 사용
  실패 → 2단계로
```

### 2단계: MCP 도구 선택 (키워드 매칭)

| 키워드 | MCP 도구 | 호출 방법 |
|--------|----------|-----------|
| PPT/프레젠테이션/슬라이드 | **Gamma** | `mcp__claude_ai_Gamma__generate` |
| 디자인/캐릭터/로고/배너 | **Canva** | `mcp__claude_ai_Canva__generate-design` 또는 `create-design-from-candidate` |
| 다이어그램/흐름도/시퀀스 | **Mermaid** | `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram` |
| Figma URL/디자인→코드 | **Figma** | `mcp__claude_ai_Figma__get_design_context` |
| 이메일/메일 | **Gmail** | `mcp__claude_ai_Gmail__gmail_create_draft` |
| 일정/캘린더 | **Google Calendar** | `mcp__claude_ai_Google_Calendar__authenticate` |
| 엑셀/CSV | **Excel** | `excel` MCP (설치 시) |
| 워크플로우/n8n | **n8n** | `n8n` MCP (설치 시) |
| AI 모델/HuggingFace | **Hugging Face** | `mcp__claude_ai_Hugging_Face__authenticate` |
| 라이브러리 문서 | **context7** | context7 MCP |
| 브라우저 테스트 | **Playwright** | playwright MCP |
| 코드 실행/진단 | **IDE** | `mcp__ide__executeCode`, `getDiagnostics` |

### 3단계: MCP 없을 때 폴백 (반드시 실행)

```
MCP 실패 시 → 텍스트만으로 끝내지 않는다. 반드시 다음 중 하나 이상 수행:

1. /artifacts 로 HTML/SVG 직접 생성 (인포그래픽, 다이어그램, 차트 등)
2. ```mermaid 코드블록으로 다이어그램 직접 생성
3. 외부 도구 프롬프트 생성 + URL 안내
4. 구조화된 마크다운으로 슬라이드 구조 생성

폴백 안내 메시지 (필수 출력):
  "[MCP 안내] {도구}가 연결되지 않았습니다.
   연결 방법:
   - claude.ai 로그인 → 설정 → 연결 (Gamma/Canva/Figma/Gmail/Calendar)
   - 또는: claude mcp add {name} -- npx ... (context7/playwright/excel/n8n)
   대안으로 {폴백 방법}을 사용합니다."
```

---

## 복합 요청 처리

PPT + 디자인 + 다이어그램이 함께 요청된 경우:

```
순서:
  1. Gamma → 전체 슬라이드 구조 + 내용 생성
  2. Canva → 커버 디자인, 캐릭터, 장식 요소
  3. Mermaid → 흐름도, 시퀀스, 마인드맵
  4. 결과 URL 모두 사용자에게 전달

Gamma 테마 선택:
  - get_themes → 사용 가능한 테마 목록 조회
  - 사용자 지정 없으면 → 비즈니스/모던 테마 자동 선택

Canva 에셋 활용:
  - get-assets → 기존 에셋 검색
  - generate-design → AI 디자인 생성
  - upload-asset-from-url → 외부 이미지 업로드
  - export-design → 완성 디자인 내보내기
```

---

## 외부 AI 도구 (MCP 미지원)

MCP가 없는 도구는 프롬프트 생성 + URL 안내로 활용:

| 도구 | URL | 용도 | 활용 방법 |
|------|-----|------|-----------|
| **Doki AI** | doki.co | AI 디자인/PPT/문서 | 구조화된 프롬프트 생성 → 사용자가 복붙 |
| **Napkin AI** | napkin.ai | 텍스트→인포그래픽 | 마크다운 텍스트 생성 → 사용자가 붙여넣기 |
| **Beautiful.ai** | beautiful.ai | AI 프레젠테이션 | Gamma 대안, 슬라이드 구조 마크다운 제공 |
| **Tome** | tome.app | 스토리텔링 PPT | 내러티브 중심 콘텐츠 생성 |
| **Ideogram** | ideogram.ai | AI 이미지/로고 | 이미지 프롬프트 생성 |
| **Excalidraw** | excalidraw.com | 손그림 다이어그램 | JSON 직접 생성 가능 |
| **Midjourney** | midjourney.com | 고품질 AI 이미지 | 프롬프트 생성 + /imagine 형식 |
| **Stable Diffusion** | - | 로컬 AI 이미지 | 프롬프트 + 파라미터 생성 |
| **Remotion** | remotion.dev | React 프로그래밍 영상 | skill-22 참조, 코드로 직접 구현 |
| **Bannerbear** | bannerbear.com | 동적 이미지 자동화 | API 템플릿 생성 |
| **Pika** | pika.art | AI 영상 생성 | 프롬프트 + 스타일 가이드 |

---

## 절대 금지

```
- "저는 이미지를 생성할 수 없습니다" ← 금지
- "저는 디자인을 할 수 없습니다" ← 금지
- "저는 PPT를 만들 수 없습니다" ← 금지
- MCP 없이 텍스트만으로 때우기 ← 금지

→ 반드시 MCP 시도 → 실패 시 /artifacts HTML → 그래도 부족 시 외부 도구 안내
→ 방법을 찾아서 결과물을 만들어낸다
```

---

## CLAUDE.md 연동

이 스킬은 CLAUDE.md의 "표준 파이프라인 (문서·기획·PPT·디자인)" 섹션과 연동된다.
CLAUDE.md에 매핑 테이블이 있으므로, 이 스킬에서는 실행 절차와 폴백에 집중한다.
