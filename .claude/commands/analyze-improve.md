---
description: "프로젝트 소스 분석 → 적용 가능한 기술·개선점 추천 (XAI·Zero Trust·RAG·이벤트 등)"
allowed-tools: Read, Glob, Grep, Bash(find:*), Bash(wc:*), Bash(python:*), Agent
---

# /analyze-improve — 프로젝트 분석 및 개선 추천

## 사용법
```text
/analyze-improve [project_path]
```

예시:
```text
/analyze-improve C:\pjt\rms
/analyze-improve C:\pjt\erp
/analyze-improve .
```

## 동작

### 1단계: 소스 분석
- 언어·프레임워크 감지 (Python/JS/Java/C#)
- 디렉토리 구조 파악
- 주요 의존성 (requirements.txt, package.json, pom.xml)
- DB 사용 여부 (SQL, NoSQL, 벡터)
- API 구조 (REST, GraphQL, gRPC)
- 테스트 커버리지
- 보안 설정

### 2단계: 개선 추천 (공통 레퍼런스 기반)
분석 결과를 기반으로 적용 가능한 기술 추천:

| 분석 결과 | 추천 기술 | 레퍼런스 |
|----------|----------|---------|
| AI 모델 사용 | XAI (SHAP/LIME) 설명 가능성 | python-toolkit-pip § XAI |
| 사용자 인증 있음 | Zero Trust (OPA/Casbin) | app-development-toolkit § Zero Trust |
| DB 쿼리 많음 | 캐시 (Redis) + 검색 (Meilisearch) | database-cache-toolkit |
| API 서버 | Rate Limiting + 모니터링 (Sentry) | devtools-essentials |
| 데이터 처리 | ETL 파이프라인 (Airflow/dbt) | app-development-toolkit § 데이터 |
| 프론트엔드 | 성능 (Core Web Vitals) + 접근성 | app-development-toolkit § 성능/a11y |
| 민감 데이터 | PETs (차등프라이버시, 합성데이터) | python-toolkit-pip § PETs |
| 이벤트 처리 | 이벤트 기반 (Kafka/Redis Streams) | realtime-streaming-toolkit |
| 테스트 없음 | pytest/jest + CI/CD | devtools-essentials § 테스트 |
| 문서 없음 | Docusaurus/Mintlify | devtools-essentials § 문서 |
| 배포 수동 | Docker + CI/CD (GitHub Actions) | deployment-infra-toolkit |
| 모바일 없음 | React Native/Flutter/Capacitor | app-development-toolkit § 모바일 |
| 수익화 안 됨 | SaaS/API 과금/구독 | monetization-toolkit |

### 3단계: 우선순위 매기기
-  즉시 (보안·안정성)
-  단기 (성능·테스트)
-  중기 (AI·자동화)
- 🔵 장기 (확장·수익화)

### 4단계: 실행 계획 생성
각 추천에 대해:
1. 필요 패키지 (`pip install` / `npm install`)
2. 예상 작업량 (시간/일)
3. 적용 코드 예시
4. 관련 레퍼런스 파일 경로

## 도메인별 특화 분석

### RMS (리스크관리시스템)
- XAI 적용 (위험도 설명)
- Knowledge Graph (거래 관계 분석)
- Event-Driven (실시간 리스크)
- 합성데이터 (테스트용)
- AI Governance (공정성)

### ERP (전사자원관리)
- 워크플로우 자동화 (Temporal)
- 데이터 통합 (Data Fabric)
- 보고서 자동화 (python-docx/openpyxl)
- 대시보드 (Streamlit/Grafana)

### ISMS-P (정보보호관리)
- 보안 스캔 자동화 (semgrep/bandit)
- 증적 자동 수집
- 컴플라이언스 체크리스트
- 취약점 관리 (Snyk/Trivy)

### 준법경영
- 문서 분석 (NLP/OCR)
- 규정 매핑 (Knowledge Graph)
- 위반 감지 (이벤트 기반)
- 감사 추적 (로깅)

## 참조
- 전체 레퍼런스 19개 (plugins/design_*/references/)
- 공통 킷 원칙: 도구는 공통, 조합은 도메인
