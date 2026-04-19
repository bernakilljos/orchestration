# Skill 설계 규칙 (Anthropic 공식 표준)

> **출처**: docs/upgrade/클로드 스킬 만들기 완벽 가이드 (2026 Anthropic 번역본, 34쪽)

## 1. 스킬이란

특정 작업/워크플로우를 Claude 에게 가르치는 **폴더 형태 명령어 모음**.
- 반복 가능한 작업에 특히 강력
- Claude.ai·Claude Code·API **이식성** 있음
- 여러 스킬 **조합 가능**

## 2. 3단계 점진적 공개 (토큰 절감)

| 단계 | 언제 로드 | 내용 |
|---|---|---|
| 1 | 항상 (시스템 프롬프트) | YAML frontmatter (`name` + `description`) |
| 2 | 작업 관련 시 | SKILL.md 본문 (전체 명령어) |
| 3 | 필요 시 | scripts/, references/, assets/ 파일 |

## 3. 표준 폴더 구조

```
your-skill-name/            # kebab-case 필수
├── SKILL.md                # 필수 (대소문자 정확)
├── scripts/                # 선택 (실행 코드)
├── references/             # 선택 (참조 문서)
└── assets/                 # 선택 (템플릿·폰트·아이콘)
```

**README.md 금지** — 모든 문서는 SKILL.md 또는 references/ 에

## 4. SKILL.md 필수 frontmatter

```yaml
---
name: your-skill-name            # kebab-case, 폴더명과 일치
description: |                    # 무엇 + 언제 (트리거) 둘 다 포함
  이 스킬이 무엇을 합니다.
  사용자가 [특정 문구]를 말할 때 사용하세요.
---
```

### 제약
- `name`: kebab-case, 공백/대문자/밑줄 금지
- `description`: 1024자 이하, XML 태그(`< >`) 금지, 'claude'/'anthropic' 예약어 금지
- 구체적 트리거 문구 + 파일 유형 언급 (해당 시)

### 선택 필드
- `license`, `compatibility`, `metadata` (author·version·mcp-server 등)

## 5. 활용 사례 3 카테고리

| 카테고리 | 예시 | 핵심 기법 |
|---|---|---|
| 1. 문서·에셋 생성 | frontend-design, pptx·xlsx 스킬 | 스타일 가이드·템플릿·체크리스트 |
| 2. 워크플로우 자동화 | skill-creator | 검증 게이트·반복 정제 |
| 3. MCP 강화 | sentry-code-review | 다중 MCP 조율·도메인 전문 지식 |

## 6. 성공 기준 (Anthropic 권장 지표)

**정량**:
- 관련 쿼리 90% 스킬 트리거
- 워크플로우 X번 도구 호출 내 완료
- MCP API 호출 실패 0건

**정성**:
- 사용자 추가 프롬프트 불필요
- 사용자 수정 없이 완료
- 세션 간 일관성

## 7. 이 프로젝트 적용 방침

우리 킷은 **2가지 스킬 형태** 혼용:
1. **Anthropic 표준 `SKILL.md`** (독립 배포용) — `plugins/_template/SKILL.md.example` 참조
2. **우리 kit 내부 `plugins/<name>/skills/skill-*.md`** (sync 대상)

### 변환 규칙
외부 공유용으로 배포 시:
- `plugins/<name>/` → `your-skill-name/SKILL.md` + `scripts/` + `references/`
- 우리 `README.md`·`SPEC.md` 는 `references/` 로 이동
- 우리 `commands/*.md` 프론트매터는 SKILL.md 본문에 흡수

### 보안 제약 (우리 kit 도 따름)
- `description` 에 XML 태그 금지
- `name` 에 `claude`·`anthropic` 금지
- mojibake(U+FFFD) 포함 시 `check-mojibake.sh` 훅이 차단

## 8. 5가지 핵심 설계 패턴 (Anthropic 검증)

| 패턴 | 언제 | 핵심 |
|---|---|---|
| **1. 순차 워크플로우** | 정해진 순서 다단계 | 단계 의존성·검증·롤백 |
| **2. 멀티 MCP 조율** | 여러 서비스 걸침 | Figma→Drive→Linear→Slack 예 |
| **3. 반복적 정제** | 품질이 반복으로 개선 | draft → check → refine loop |
| **4. 컨텍스트 인식 선택** | 상황별 다른 도구 | 파일 크기·유형별 분기 |
| **5. 도메인 특화 인텔리전스** | 단순 도구 접근 이상 | 컴플라이언스·감사 추적 |

## 9. 테스트 3영역

### 트리거 테스트
- ✅ 명확한 작업에서 트리거
- ✅ 다른 표현으로 바꾼 요청에서도 트리거
- ❌ 관련 없는 주제에서는 트리거 안 됨

### 기능 테스트
- 유효한 결과물 / API 성공 / 에러 처리 / 엣지 케이스

### 성능 비교
- 스킬 있/없을 때 토큰·API 실패·질문 수

## 10. 트러블슈팅 (흔한 문제)

| 증상 | 원인 | 해결 |
|---|---|---|
| "SKILL.md 찾을 수 없음" | 파일명 부정확 | `SKILL.md` 정확히 (대소문자) |
| "잘못된 프론트매터" | YAML `---` 구분자 누락 | 앞뒤 `---` 추가 |
| "잘못된 스킬 이름" | 공백·대문자 | kebab-case |
| 트리거 부족 | description 모호 | 구체 키워드·트리거 문구 추가 |
| 트리거 과잉 | description 너무 광범 | "X 할 때만", 부정 트리거 추가 |
| 명령어 안 따름 | 장황·모호 | 간결·중요 상단·명확 언어 |
| 모델 게으름 | 품질 저하 | "철저히"·"속도보다 품질" 명시 |
| 대용량 컨텍스트 | SKILL.md 과대 | ≤5000단어, 나머지 references/ |

## 11. 성능 한계 (Anthropic 가이드)
- SKILL.md **5,000단어 이하** 권장
- 동시 활성 스킬 **20~50개 이하**
- description **1024자 이하**
- 더 많으면 "스킬 팩" 으로 묶기

## 12. 빠른 체크리스트 (Anthropic 부록 A)

**시작 전**:
- [ ] 구체 활용 사례 2~3개 정의
- [ ] 도구 파악 (내장/MCP)
- [ ] 폴더 구조 계획

**개발 중**:
- [ ] 폴더명 kebab-case
- [ ] SKILL.md 정확한 철자
- [ ] YAML `---` 구분자
- [ ] name·description 규칙 준수
- [ ] XML 태그 없음
- [ ] 명령어 명확·실행 가능
- [ ] 에러 처리·예시 포함

**업로드 전**:
- [ ] 명확한 작업에서 트리거 테스트
- [ ] 다른 표현 요청에서도 트리거
- [ ] 관련 없는 주제에서 트리거 안 됨
- [ ] 기능 테스트 통과
- [ ] 도구 연동 작동

**업로드 후**:
- [ ] 실제 대화 테스트
- [ ] 과소/과다 트리거 모니터
- [ ] 피드백 수집
- [ ] 버전 업데이트

## 13. YAML frontmatter 전체 필드 (부록 B)

```yaml
---
name: skill-name-in-kebab-case       # 필수
description: |                         # 필수, 1024자 이하
  무엇 + 언제 (트리거)
license: MIT                           # 선택
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"  # 선택
metadata:                              # 선택
  author: 회사명
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
  support: support@example.com
---
```

## 14. 참조

- PDF: `docs/upgrade/클로드 스킬 만들기 완벽 가이드(한국어 번역본).pdf` (34쪽)
- 파트너 레포: `github.com/anthropics/skills`
- skill-creator: Claude.ai 내장 + Claude Code 다운로드
- 템플릿: `plugins/_template/SKILL.md.example`
- 훅: `.claude/hooks/check-mojibake.sh` (한글 깨짐 방지)
- 공통 규칙: `.claude/rules/plugin-structure.md` · `frontmatter.md`
