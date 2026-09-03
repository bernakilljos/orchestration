# 법률 & 컴플라이언스 공통 도구모음 (80+ tools)

> **용도**: 계약·규정·지적재산·감사 관리 시 참고
> **범위**: 계약관리 ~ 규정준수 ~ 법률AI ~ 한국 법률서비스
> **관리**: orchestration_v1 reference (sync 대상 아님)

---

## 1. 계약 관리 (Contract Lifecycle Management, CLM)

| 도구 | 특징 | 주요 고객 | 가격 | API |
|------|------|----------|------|-----|
| **DocuSign CLM** | 계약 생성→서명→관리 플랫폼, eSignature 통합 | Salesforce, Oracle 연계 | $500+/월 | REST API |
| **PandaDoc** | 노코드 계약 템플릿, 협상 추적 (redline) | 중소기업 선호 | $150+/월 | REST API, Zapier |
| **Ironclad** | AI 계약 분석 (위험도 스코어), 자동 갱신 알림 | 엔터프라이즈 (구글, IBM) | 요청 시 | REST API |
| **Juro** | 블록체인 기반 계약, 자동 협상 | 스타트업, 벤처 | $200+/월 | REST API |
| **ContractPodAi** | AI 계약 분석 + 리뷰 | 법무팀 협업 | $400+/월 | REST API |
| **Zuora Billing** | 구독 기반 계약 + 청구 자동화 | SaaS 업체 | $1500+/월 | REST API |
| **Stripe Billing** | SaaS 청구, 구독 관리 | 스타트업 (무료층) | 종량제 | REST API |

### DocuSign CLM API (Node.js)
```bash
npm install docusign-esign       # 공식 SDK
curl https://api.docusign.com/v2.1/accounts/{accountId}/envelopes \
```

### PandaDoc 템플릿 자동화
```bash
pip install pandadoc            # Python 비공식 라이브러리
curl https://api.pandadoc.com/v1/documents \
  -X POST \
  -d '{"template_id": "xxx", "recipients": [{"email": "user@example.com"}]}'
```

---

## 2. 전자서명 (eSignature)

| 도구 | 형식 | 법적 효력 | 국가 지원 | 가격 |
|------|------|----------|---------|------|
| **DocuSign** | PDF/Word |  ESIGN Act (미국), eIDAS (EU), 한국 | 130+ | $20/월+ |
| **HelloSign** | PDF 중심 |  유사 | 50+ | $15/월+ |
| **SignNow** | 모바일 최적화 |  | 50+ | $9.99/월+ |
| **Adobe Sign** | Creative Cloud 통합 |  | 50+ | $25/월+ |
| **Zoho Sign** | CRM 통합 (Zoho 생태계) |  | 30+ | $10/월+ |
| **Acrobat Sign** | Adobe 제품군 |  | 50+ | $25/월+ |
| **Secured Signing** | 한국 전자서명법 준수 |  (한국 공식) | 한국 | 협의 |
| **GPKi (금융결제원)** | 공인인증서 기반 |  (한국 법인) | 한국 | 협의 |

### DocuSign eSignature API
```bash
npm install docusign-esign
curl https://demo.docusign.net/restapi/v2.1/accounts/{accountId}/envelopes \
  -X POST \
  -d '{
    "documents": [{"documentBase64": "..."}],
    "recipients": [{"email": "signer@example.com", "name": "John Doe"}],
    "status": "sent"
  }'
```

### Adobe Sign API
```bash
curl https://api.na1.adobesign.com/api/rest/v6/transientDocuments \
  -X POST \
  -F "File=@contract.pdf"
```

---

## 3. GDPR & 개인정보 관리

| 도구 | 기능 | 커버리지 | 가격 | 특징 |
|------|------|---------|------|------|
| **OneTrust** | 데이터 거버넌스, 컴플라이언스 자동화 | GDPR, CCPA, HIPAA 등 | $10k+/년 | 대규모 기업 |
| **TrustArc** | 감사, 인증, 컴플라이언스 관리 | 12+ 규제 | $8k+/년 | SOC2, ISO27001 |
| **Cookiebot** | 쿠키 동의 배너 (CMP) | GDPR, ePrivacy | $50+/월 | 웹사이트용 |
| **Osano** | GDPR, HIPAA, CCPA 자동화 | 미국/EU | $200+/월 | 스타트업 친화 |
| **iubenda** | 약관, 쿠키배너, 개인정보 | EU/글로벌 | $10+/월 | 웹사이트 통합 |
| **Termly** | 약관, 개인정보보호정책 자동생성 | 50+ 규제 | $99/년+ | 자동 갱신 |
| **DataGuidance** | 규제 상담, 기술문서 | 글로벌 | 정액 | 법률 자문 |

### Cookiebot 설치 (JavaScript)
```html
<!-- 웹사이트 헤드에 추가 -->
<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js" 
  data-cbid="$DOMAIN_ID" data-blockingmode="auto"></script>
```

### OneTrust API
```bash
curl https://api.onetrust.com/api/v1/audit \
```

### iubenda 약관 생성 (REST)
```bash
curl https://www.iubenda.com/api/privacypolicy \
  -X POST \
  -d '{
    "language": "ko",
    "policies": ["analytics", "marketing"],
    "website": "https://example.com"
  }'
```

---

## 4. 약관 & 개인정보보호정책 생성

| 도구 | 출력 | 자동 갱신 | 가격 | 한국 |
|------|-----|---------|------|------|
| **Termageddon** | PDF, HTML |  (법규 변경시) | $99/년+ | 영어 중심 |
| **TermsFeed** | PDF, HTML, 워드프레스 |  | $59/년+ | 다국어 (한국어 O) |
| **Iubenda** | 모든 언어 동적 |  | $10+/월 |  한국어 지원 |
| **GetTerms** | 노코드 생성 |  | $79/월+ | 영어 중심 |
| **Otherent** | 한국 법률 표준 | 수동 | 협의 |  한국전문 |

### TermsFeed API (자동 생성)
```bash
curl https://www.termsfeed.com/api/v1/generate \
  -X POST \
  -d '{
    "policy": "privacy",
    "language": "ko",
    "website_url": "https://example.com"
  }'
```

### iubenda 웹사이트 통합
```html
<!-- 자동 정책 로드 -->
<iframe src="https://www.iubenda.com/privacy-policy/$POLICY_ID" 
  frameborder="0" width="100%" height="600"></iframe>
```

---

## 5. 규정준수 & 감사 (Compliance)

| 도구 | 표준 | 자동화 | 가격 | 클라우드 |
|------|------|--------|------|---------|
| **Vanta** | SOC2, ISO27001, HIPAA, GDPR |  자동 증거수집 | $500+/월 | AWS, GCP, Azure |
| **Drata** | SOC2, ISO27001, HIPAA |  자동 감사 | $400+/월 | 다중클라우드 |
| **Secureframe** | SOC2, ISO27001, HIPAA, FedRAMP |  최고 자동화 | $500+/월 | 엔터프라이즈 |
| **Sprinto** | SOC2, ISO27001, HIPAA |  차세대 감사 | $300+/월 | 신흥 강자 |
| **AuditBoard** | 내부감사, 위험관리 |  협업 | $500+/월 | 대기업 |
| **LogicGate** | GRC (Governance, Risk, Compliance) |  자동 워크플로우 | $400+/월 | 위험도 시각화 |

### Vanta API (Python)
```bash
pip install vanta-api           # 비공식
curl https://api.vanta.com/v1/monitoring \
```

### Drata 자동 감사 설정
```bash
# AWS 역할 자동 연결 (SOC2 증거)
curl https://api.drata.com/v1/connections/aws \
  -X POST \
  -d '{"aws_account_id": "123456789", "external_id": "drata"}'
```

---

## 6. 법률 AI & 자동화

| 도구 | 특화 | 기술 | 가격 | 정확도 |
|------|------|------|------|--------|
| **Harvey** | 법률 연구, 계약 분석 (LLM) | GPT 기반 법률 모델 | 요청 시 | 90%+ |
| **CoCounsel** | 발견(eDiscovery), 법률 조사 | 법률 데이터 학습 | $500+/월 | 95%+ |
| **Casetext** | 판례 검색, 법률 문서 분석 | 법률 NLP | $50+/월 | 92%+ |
| **LexisNexis** | 대규모 법률 데이터베이스 | 전통 검색 + AI | 협의 | 전통 기준 |
| **Westlaw** | 판례, 법령, 문헌 | 전통 + AI 강화 | 협의 | 전통 기준 |
| **OpenAI + Legal Prompts** | 계약 초안, QA | GPT4 커스텀 | $20/월 | 80%+ (감수 필요) |

### CoCounsel API (LexisNexis)
```bash
curl https://api.cocounsel.com/v1/analyze \
  -X POST \
  -d '{
    "document_url": "https://example.com/contract.pdf",
    "analysis_type": "contract_review",
    "questions": ["주요 위험 조항은?", "계약 기간은?"]
  }'
```

### Casetext API (법률 검색)
```bash
pip install casetext-api
curl https://api.casetext.com/v1/search \
  -d '{"query": "소유권 이전", "jurisdiction": "한국"}'
```

---

## 7. 지적재산 (Intellectual Property)

| 서비스 | 범위 | 국가 | 특징 | API |
|--------|------|------|------|-----|
| **KIPRIS** | 특허, 실용신안, 디자인 | 한국 | 특허청 공식 DB | REST API |
| **WIPO** | 국제특허 (PCT) | 글로벌 | 국제 특허협약 | REST API |
| **Google Patents** | 공개특허 검색 | 글로벌 | 무료, 분석 도구 | 웹 스크래핑 |
| **PatSnap** | 특허 경쟁 분석 | 글로벌 | AI 기반 인사이트 | REST API |
| **Espacenet** | EU 특허 | 유럽 | 무료 | REST API |
| **USPTO** | 미국 특허 | 미국 | 공식 DB | REST API |
| **JPO (일본)** | 일본 특허 | 일본 | 일본 특허청 | REST API |

### KIPRIS API (한국 특허청)
```bash
# 공개키 신청 필수 (특허청 웹사이트)
curl "https://www.kipris.or.kr/openapi/searchCustom" \
  -H "X-API-KEY: $API_KEY" \
  -d '{
    "query": "인공지능",
    "docdbCode": "KR",
    "numOfRows": 10
  }'
```

### WIPO PCT 검색
```bash
curl "https://pct.wipo.int/api/search" \
  -d '{
    "query": "machine learning",
    "publicationNumber": "WO2023*"
  }'
```

### Google Patents (웹 스크래핑)
```python
from selenium import webdriver
driver = webdriver.Chrome()
driver.get("https://patents.google.com/?q=python&country=KR")
# Selenium으로 파싱 또는 공식 API 기다리기
```

### PatSnap API
```bash
curl https://api.patsnap.com/patent/search \
  -d '{"keywords": "quantum computing", "country": "US"}'
```

---

## 8. 한국 법률 & 규정 데이터

| 서비스 | 주요 데이터 | API | 특징 |
|--------|-----------|-----|------|
| **국가법령정보센터** | 법률, 시행령, 규칙 (모든 법 완전 수록) | REST API | 법제처 공식 |
| **대법원 종합법령정보** | 판례, 판사 정보 | 없음 (웹전용) | 판례 900만+ |
| **법제처 API** | 법령 데이터, 행정예규 | REST API | 공공데이터포털 |
| **헌법재판소** | 헌법 판례 | 웹 전용 | 위헌법률 판정 |
| **국가인권위원회** | 인권 결정례 | 웹 전용 | 차별, 인권침해 |
| **금융감독위원회** | 금융규정, 공시정보 | REST API | 공공데이터포털 |
| **국세청** | 세법, 절차 | 없음 | 홈텍스 포털 |

### 국가법령정보센터 API
```bash
# 공공데이터포털에서 키 신청
curl "https://www.law.go.kr/API/SearchSTac" \
  -H "ServiceKey: $SERVICE_KEY" \
  -d '{
    "query": "개인정보보호법",
    "type": "법령",
    "pageNo": 1
  }'
```

### 법제처 법령 조회
```bash
# 공공데이터포털
curl "https://www.data.go.kr/api/15042959/execute-layer" \
  -d '{
    "query": "근로기준법",
    "page": 1
  }'
```

---

## 9. 감사 & 로그 관리

| 도구 | 기능 | 특징 | 가격 | 준거 |
|------|------|------|------|------|
| **AuditBoard** | 내부감사, 위험도 추적, 보증 | 협업 감사 워크플로우 | $500+/월 | SOX, COSO |
| **LogicGate** | GRC (거버넌스·위험·컴플라이언스) | 원 플랫폼 GRC | $400+/월 | ISO, COBIT |
| **ServiceNow GRC** | 위험도, 컴플라이언스, 감사 | 엔터프라이즈 플랫폼 | $1000+/월 | 모든 표준 |
| **Domo** | BI + 감사 대시보드 | 실시간 데이터 시각화 | $300+/월 | 커스텀 |
| **Splunk** | 로그 수집, 보안 이벤트 | SIEM (보안 정보) | $100+/월 | SOC2, HIPAA |
| **Datadog** | 모니터링 + 감시 | 클라우드 네이티브 | $15+/월 | AWS, GCP, Azure |

### AuditBoard API
```bash
curl https://api.auditboard.com/v1/audit-tasks \
```

### Splunk 로그 수집
```bash
# 에이전트 설치
wget -O splunkforwarder.tgz 'https://www.splunk.com/...'
tar xzvf splunkforwarder.tgz
./splunkforwarder/bin/splunkd start
```

### ServiceNow GRC (REST)
```bash
curl https://$INSTANCE.service-now.com/api/now/v1/risk \
```

---

## 10. 문서 분석 & NLP (법률 전문 NER)

| 도구 | 특화 | 언어 | 정확도 | 가격 |
|------|-----|------|--------|------|
| **spaCy** (법률 모델) | 개체명 인식 (법률 용어), 의존 구문 분석 | 다국어 (한국어O) | 85-90% | 오픈소스 |
| **KoNLPy** | 한국어 NLP (명사, 술어 추출) | 한국어 전문 | 80-85% | 오픈소스 |
| **Hugging Face transformers** | BERT 기반 법률 분류 | 다국어 | 90%+ | 오픈소스 |
| **LawBreaker (한국)** | 판례 텍스트 분석, 법률용어 | 한국어 | 90%+ | API 협의 |
| **Legal Text Summarizer** | 법률 문서 요약 | 영어/한국어 | 80%+ | 커스텀 |

### spaCy 법률 NER
```bash
pip install spacy
python -m spacy download en_core_web_sm

# 법률 약관 분석
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp("The party shall indemnify the other party...")
for ent in doc.ents:
    print(f"{ent.text} ({ent.label_})")  # 계약당사자, 의무 등
```

### KoNLPy (한국어 법률 문서)
```bash
pip install konlpy
from konlpy.tag import Okt
okt = Okt()
text = "개인정보보호법 제15조에 따라..."
nouns = okt.nouns(text)  # 명사 추출 (법률용어)
```

### Hugging Face 법률 텍스트 분류
```bash
pip install transformers
from transformers import pipeline
classifier = pipeline("text-classification", 
  model="nlpaueb/legal-bert-base-uncased")
result = classifier("This agreement shall commence...")
# {'label': 'contract_obligation', 'score': 0.95}
```

---

## 11. 종합 비교 표

| 기준 | CLM 추천 | eSignature 추천 | 컴플라이언스 추천 | 법률AI 추천 | 한국 추천 |
|------|---------|---|---|---|---|
| **무료** | 없음 (평가판 O) | HelloSign 스타트업 패스 | Termly 기본 | GPT + 프롬프팅 | KIPRIS, 국가법령정보 |
| **엔터프라이즈** | Ironclad, DocuSign | Adobe Sign, Secured Signing | Vanta, Secureframe | CoCounsel, Harvey | 대형로펌 (내부) |
| **스타트업** | PandaDoc, Juro | SignNow, HelloSign | Osano, Sprinto | OpenAI + 커스텀 | TermsFeed + KIPRIS |
| **한국 법률** | 없음 (영문 변경) | Secured Signing, GPKi | TrustArc + 국가법령정보 | 개별 프롬프팅 |  국가법령정보 + 법제처 |
| **AI 강점** | ContractPodAi, Ironclad | 없음 | Vanta (자동증거) | Harvey, CoCounsel | 없음 (LLM 외국 의존) |

---

## 12. 설치 & 통합 예

### DocuSign + Salesforce 자동화
```bash
# Salesforce에서 DocuSign 앱 설치 (AppExchange)
# 계약 생성 → DocuSign 서명 → Salesforce 업데이트 자동화
```

### OneTrust + Slack 알림
```bash
# OneTrust 감사 이벤트 → Slack 알림
curl https://hooks.slack.com/services/YOUR/WEBHOOK \
  -X POST \
  -d '{
    "text": "GDPR 컴플라이언스: 3주 안에 갱신 필요",
    "channel": "#legal"
  }'
```

### KIPRIS 특허 모니터링
```python
# 경쟁사 특허 자동 감시
import requests
response = requests.get(
  "https://www.kipris.or.kr/openapi/searchCustom",
  headers={"X-API-KEY": "$API_KEY"},
  json={"query": "머신러닝", "docdbCode": "KR"}
)
patents = response.json()["patents"]
# 매일 새 특허 감지 → 이메일 알림
```

### 국가법령정보 자동 조회
```bash
# 법령 개정 모니터링
curl "https://www.law.go.kr/API/SearchSTac" \
  -d '{
    "query": "개인정보보호법",
    "type": "법령"
  }' | jq '.laws[0].updated_date'
```

---

## 참조

- **DocuSign**: https://developers.docusign.com/
- **OneTrust**: https://www.onetrust.com/
- **KIPRIS (특허청)**: https://www.kipris.or.kr/openapi/
- **국가법령정보센터**: https://www.law.go.kr/
- **법제처 공공데이터**: https://www.data.go.kr/ (검색: "법령")
- **spaCy 법률 모델**: https://spacy.io/
- **KoNLPy**: http://konlpy.org/
- **Harvey (법률AI)**: https://www.harvey.ai/
- **Vanta**: https://www.vanta.com/
