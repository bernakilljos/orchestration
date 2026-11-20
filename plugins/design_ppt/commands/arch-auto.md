---
description: "주제·문서 목적을 보고 알맞은 도식 선택 — 기술 아키텍처(C4·배포·시퀀스·데이터흐름·보안 경계)와 개념도(마인드맵·레이어·치트시트)"
allowed-tools: Bash(where:*), Bash(claude mcp list:*), Write, Bash(python:*)
---

## Context
- 개념 정리용 패턴 (기존):
  - mindmap (방사형) — `arch-mindmap`
  - layered (레이어 케이크) — `arch-layered`
  - cheatsheet (3컬럼) — `arch-cheatsheet`
- **기술 아키텍처 패턴 (R342 · 2026-11-20 추가)** — 실제 시스템을 고객·검토자·개발자에게 설명할 때:
  - C4 System Context · Container · Component · Dynamic(순서 있는 호출) · Deployment
  - Data-flow / Storage (DFD) · Trust boundary (보안 경계·키 범위·유입/유출) · Provider fallback (AI·외부 서비스 우선순위)
- 근거 (본문 확인 2026-11-20): c4model.com/diagrams (Context·Container·Component·Dynamic·Deployment) ·
  Azure Well-Architected «Design architecture diagrams» (화살표 필수 · 선 의미를 쓰면 범례 · 경계 명시 · 색만으로 의미 전달 금지 · DFD 는 소스·싱크·변환·저장·데이터 분류)

## Your task

주제: `$ARGUMENTS`

---

### Step 0 — 문서 목적·유형 분류 (먼저)

| 독자·목적 | 문서 유형 | 우선 도식 |
|---|---|---|
| 임원 보고 · 고객 설명 | 결론 + 구조 한 장 | System Context → (필요 시) Container |
| 개발자 설계 검토 | 구성·호출 | Container · Component · Dynamic/Sequence |
| 운영자 설치·배포 | 장비·네트워크 | Deployment (네트워크 영역·방화벽·필수/선택 서버) |
| 보안 검토 | 경계·키·인증 | Trust boundary + DFD (데이터 분류) |
| 데이터·저장 설명 | 저장·동기화·실패 경로 | DFD / Storage (실패 시 응답 코드 포함) |
| AI·외부 연동 | 우선순위·조건부 호출 | Provider fallback (조건·미설정 동작) |
| 개념·학습·온보딩 | 개념 정리 | mindmap · layered · cheatsheet (기존) |

모든 슬라이드에 그림을 넣지 않는다 — 구조·흐름·배포·데이터·경계가 핵심인 장에만.

### Step 1 — 도식 규칙 (기술 아키텍처일 때 필수)

1. **한 그림 = 한 관점**: 구조(어디에 무엇) · 처리 흐름(언제 무엇을 호출) · 배포(어느 장비·네트워크) · 데이터(어디에 저장) 를 한 그림에 섞지 않는다. 상시 구성 관계와 1·2·3 번호 호출 흐름을 같은 그림에 그리면 혼동 → Context/Container 와 Dynamic 을 나눈다.
2. **화살표**: 항상 방향 · 라벨에 프로토콜/포트·조건(필수/선택·실패 시) · 양방향은 두 흐름으로 · 실선/점선 의미를 쓰면 범례.
3. **경계**: 내부/외부/고객사/선택 구성은 경계 상자로 구분 (색만으로 구분 X · 라벨 병기).
4. **사실 근거**: 노드·연결은 원본 문서·코드·설정에 있는 것만 · 근거 없는 연결선·포트·제품명 금지 (모르면 그리지 않고 «미확인» 표기).
5. **정보 밀도**: 긴 표가 반복되면 «다이어그램 1개 + 핵심 3~5줄 + 상세표는 부록».
6. **편집 가능성**: PowerPoint native shape·connector·텍스트 우선 · 페이지 전체를 그림 한 장으로 평면화 금지.
7. **검수**: 렌더된 슬라이드 이미지를 보고 화살표 연결·방향·잘림·겹침·한글 폰트·범례를 확인 (`skill-ppt-pitfalls.md` § 15). OCR·shape 개수만으로 PASS 금지.
8. **사실 계약 (R343)**: 입력(요구서·소스·설정·DB 스키마·배포 산출물)에서 문장마다 **사실 / 해석 / 권고 / 가정 / 미확인** 구분 · 구현된 동작(코드) · 설계 의도(문서) · 계획 기능을 섞지 않음 (소스 없는 장래 기능을 «제공» 으로 쓰지 않음) · 공식 레퍼런스는 표현 근거일 뿐 그 제품 구현의 증거가 아님 · 문서끼리 다르면 조용히 맞추지 말고 불일치로 표시.
9. **문구**: 주어·행위·조건·결과·예외·단위를 분명히 · 용어·버전 일관 · 근거 없는 수치·«혁신적·완벽한·전면 자동» 금지 · 고객 발표와 개발자 설계는 밀도·톤을 다르게.
10. **하드코딩 금지**: 특정 제품명·포트·장수·구성요소 수·색·카드 배치를 규칙에 넣지 않는다 — 모두 그 문서의 검증된 입력에서만.

### Step 2 — 패턴 판단 로그

```text
 주제: <topic>
🔍 독자·목적: <임원/고객/개발/운영/보안>
🔍 관점: <구조/흐름/배포/데이터/경계/개념>
 선택: <C4 Context | Container | Component | Dynamic | Deployment | DFD | Trust boundary | Provider fallback | mindmap | layered | cheatsheet>
   이유: <한 문장> · 근거 자료: <원본 문서/코드 경로>
```

### Step 3 — 선택된 패턴 실행

- 개념 패턴: mindmap → `skill-arch-mindmap` + Mermaid · layered → `skill-arch-layered` · cheatsheet → `skill-arch-cheatsheet`
- 기술 패턴 (Container · Dynamic): **`python .claude/scripts/arch-diagram-pptx.py <spec.json> <out.pptx>`** (R343 정본 엔진 · native shape·connector 편집 가능)
  - spec = 사실 원본: 노드(id·label·kind·boundary·**source**) · 연결(from·to·label·optional·**source**) · Dynamic 은 participants·steps.
  - source 없는 요소 = 거부 (`--allow-unverified` 면 그림에 «[미확인]» 표시 · 범례 자동) · 끝점 없는 연결·id 중복 = 거부 · 배치는 연결 관계로 자동 (고정 좌표 없음).
  - 출력 JSON 의 `claims` = 요소 → 근거 대조표 (보고서에 그대로) · 검증만: `--check <spec.json>`.
  - 그 밖의 도식(Deployment·DFD·Trust boundary 등)은 같은 규칙으로 python-pptx 또는 `/design_ppt` HTML 파이프라인 · Mermaid 는 초안·검증용
- 사용자가 패턴을 명시하면(`C4로`, `시퀀스로`, `마인드맵으로` …) 그것을 우선.

### Step 4 — 결과 보고

```text
 자동 선택 결과
- 패턴: <name> · 독자: <…>
- 근거 자료: <경로>
- 산출물: outputs/arch/<pattern>-<slug>-<date>.<ext>
- 검수: 렌더 이미지 확인 <예/아니오> · 근거 없는 연결 0 · 범례 <있음/불필요>
```
