# Testing & QA 공통 도구 레퍼런스

> **목적**: 테스트·품질보증 관련 공통 도구 카탈로그 (도메인 무관, 모든 프로젝트 공통)
> **원칙**: 도구는 공통, 조합·통합은 도메인에서
> **범위**: Python · JavaScript/TypeScript · 브라우저 E2E · API · 성능 · 보안 · 코드 품질 · 정적 분석 · 데이터 생성 · CI/CD
> **총 도구 수**: 180+ (13 카테고리)

---

## 1. Python 단위/통합 테스트 프레임워크 (20+)

### 핵심 프레임워크
```bash
pip install pytest             # 가장 광범위 — fixtures, parametrize, markers, plugins, 재귀적 발견
pip install unittest           # Python 내장 — xUnit 스타일 (기초 사용 시)
pip install nose2              # unittest 대안 — 더 간단한 문법, 플러그인 체계
pip install hypothesis         # Property-based testing — 자동 엣지 케이스 생성
pip install tox                # 다중 환경 테스트 (Python 3.9~3.14, 가상환경 자동 생성)
pip install nox                # tox 보다 빠르고 유연 (pyproject.toml 기반)
pip install pytest-asyncio     # async/await 테스트 지원
pip install anyio              # 비동기 프레임워크 중립 (asyncio/trio/curio)
```

### 픽스처·데이터 생성
```bash
pip install faker              # 가짜 데이터 생성 (이름, 주소, 이메일, 카드, JSON)
pip install factory_boy        # ORM fixture 팩토리 (Django, SQLAlchemy)
pip install polyfactory        # Pydantic/Dataclass 팩토리 (타입 힌트 기반)
pip install mimesis            # Faker 경량 대안 (45+ 로케일)
```

### 목(Mock)·스텁·시뮬레이션
```bash
pip install responses          # HTTP mock (requests 라이브러리)
pip install httpretty          # HTTP 캡처·재생 (소켓 수준)
pip install vcrpy              # "카세트" 패턴 HTTP 기록
pip install freezegun          # 시간 mocking (datetime/timezone)
pip install mongomock          # MongoDB 메모리 mock
pip install fakeredis          # Redis 메모리 mock
pip install testcontainers     # Docker 기반 의존성 (PostgreSQL, MySQL, Kafka 등)
```

### 커버리지·프로파일링
```bash
pip install coverage           # 코드 커버리지 측정 + HTML 보고서
pip install pytest-cov         # pytest 플러그인 (coverage 통합)
pip install pytest-benchmark   # 성능 마이크로벤치마크
pip install pytest-profiling   # CPU/메모리 프로파일링
pip install memory-profiler    # 메모리 사용량 추적
```

---

## 2. JavaScript/TypeScript 단위/통합 테스트 (25+)

### 핵심 프레임워크
```bash
npm install --save-dev jest                    # 가장 광범위 — snapshot, coverage, watch, mocking
npm install --save-dev vitest                  # Vite 네이티브 (매우 빠름, ESM 지원)
npm install --save-dev mocha                   # 유연한 구조 (test runner)
npm install --save-dev chai                    # 가독성 높은 assertion (mocha 보완)
npm install --save-dev jasmine                 # 포괄적 (빌트인 spy/mock/fake)
npm install --save-dev @vitest/ui              # Vitest UI (브라우저 대시보드)
npm install --save-dev @jest/reporters         # Jest 커스텀 리포터
```

### 컴포넌트 테스트 (React/Vue/Angular/Svelte)
```bash
npm install --save-dev @testing-library/react            # React 유저 중심 테스트
npm install --save-dev @testing-library/vue              # Vue 유저 중심 테스트
npm install --save-dev @testing-library/angular          # Angular 유저 중심 테스트
npm install --save-dev @testing-library/svelte           # Svelte 유저 중심 테스트
npm install --save-dev @testing-library/dom              # DOM 유틸 (코어)
npm install --save-dev @testing-library/user-event       # 사용자 상호작용 시뮬레이션
npm install --save-dev testing-library-preact            # Preact 컴포넌트 테스트
npm install --save-dev @storybook/test-runner            # Storybook 스토리 테스트 자동화
```

### 목·스텁·HTTP 모킹
```bash
npm install --save-dev msw                     # Mock Service Worker (가로채기 수준)
npm install --save-dev jest-mock-extended      # Jest 용 고급 mock
npm install --save-dev sinon                   # spy/stub/mock (레거시·다재다능)
npm install --save-dev nock                    # HTTP mock (http/https)
npm install --save-dev supertest               # HTTP assertion (Express/Koa)
npm install --save-dev node-mocks-http         # req/res mock (Node.js)
```

### 스냅샷·스토리북
```bash
npm install --save-dev jest-snapshot-serializer    # 스냅샷 포맷 커스터마이징
npm install --save-dev @storybook/addon-storyshots # Storybook 스토리 스냅샷
npm install --save-dev jest-serializer-html        # HTML 스냅샷
```

### 비동기·Promise 테스트
```bash
npm install --save-dev jest-extended           # 추가 matchers (toReject 등)
npm install --save-dev p-queue                 # Promise 큐 테스트
```

---

## 3. 브라우저 E2E 테스트 (15+)

### Playwright (권장 — 교차 브라우저·빠름)
```bash
npm install --save-dev @playwright/test        # Playwright Test (기본)
npm install --save-dev playwright              # Playwright Core (스크립트 용)
npm install --save-dev @playwright/test-ct     # Component Testing (React/Vue/Angular)
npm install --save-dev playwright-extra-sharp  # 스크린샷 압축
npm install --save-dev playwright-visual-comparison  # 시각적 회귀
```

### Cypress (개발 친화적)
```bash
npm install --save-dev cypress                 # 실시간 리로드, 디버깅
npm install --save-dev cypress-image-snapshot  # 시각적 비교
npm install --save-dev cypress-axe             # 접근성 테스트 (axe)
npm install --save-dev @cypress/webpack-dev-server  # Webpack 지원
```

### 기타 E2E
```bash
npm install --save-dev puppeteer               # Chrome 컨트롤 (Playwright 보다 가볍지만 Chrome-only)
npm install --save-dev webdriverio             # WebDriver 표준 (모든 브라우저)
npm install --save-dev testcafe                # 추상화 높음 (스크립트 기반)
npm install --save-dev nightwatch              # WebDriver + 문법 간단
pip install selenium                           # Python WebDriver (교차 언어)
```

### 모바일 E2E
```bash
pip install appium                             # Appium — iOS/Android 네이티브 앱 테스트
npm install --save-dev detox                   # React Native E2E (그레이박스)
npm install --save-dev maestro                 # 모바일 클라우드 테스트 (SaaS)
```

---

## 4. API 테스트 (15+)

### 상호작용·검증
```bash
pip install httpx                              # HTTP 클라이언트 (async 지원)
pip install requests                           # HTTP 요청 (사실상 표준)
pip install httpretty                          # HTTP mock (위에서 중복)
pip install responses                          # requests mock (위에서 중복)
npm install --save-dev supertest               # Express/Koa HTTP assertion (위에서 중복)
npm install --save-dev rest-assured            # HTTP 유창한 assertion
npm install --save-dev chai-http                # Chai HTTP 플러그인
pip install pydantic-extra-types               # Pydantic 검증 (JSON 스키마)
```

### OpenAPI·규약 검증
```bash
pip install schemathesis                       # OpenAPI 자동 fuzzing (하이브리드 테스트)
pip install openapi-spec-validator             # OpenAPI/Swagger JSON 스키마 검증
pip install fastjsonschema                     # JSON 스키마 고속 검증
npm install --save-dev swagger-ui-dist         # Swagger UI (서빙)
```

### API 설계·문서·목
```bash
pip install dredd                              # API 블루프린트 검증 (테스트)
npm install --save-dev dredd-cli                # Dredd CLI
pip install connexion                          # OpenAPI 기반 자동 라우팅 + mock
npm install --save-dev prism-cli                # Stoplight Prism (OpenAPI mock 서버)
pip install apistar                            # REST API 프레임워크 (자동 문서)
```

### 계약 테스트
```bash
pip install pact-python                        # Pact — 마이크로서비스 계약 (Python)
npm install --save-dev @pact-foundation/pact   # Pact JS
npm install --save-dev jest-pact                # Jest + Pact 통합
```

---

## 5. 성능·부하 테스트 (15+)

### 개발자 친화적
```bash
pip install k6                                 # Grafana K6 (JavaScript, CI-native)
npm install --save-dev k6                      # K6 npm 패키지
pip install locust                             # Locust (Python, 분산, 웹 UI)
npm install --save-dev artillery               # Artillery (Node.js, YAML 시나리오, 간단)
pip install vegeta                             # Vegeta (Go, CLI, 간단한 부하)
npm install --save-dev autocannon              # Autocannon (Node.js, HTTP 벤치)
```

### 엔터프라이즈급
```bash
pip install jmeter                             # Apache JMeter (Java, GUI, 복잡한 시나리오)
pip install gatling                            # Gatling (Scala, 매우 빠름, CI-native)
pip install taurus                             # BlazeMeter Taurus (JMeter 추상화)
pip install neoload                            # NeoLoad (상업, GUI)
```

### HTTP 벤치마크
```bash
pip install wrk2                               # wrk (Go, C 성능, 정확한 백분위수)
pip install ghz                                # ghz (gRPC 벤치)
npm install --save-dev oha                     # Oha (Rust, 고속, HTTP)
```

### 프로파일링·메트릭
```bash
pip install py-spy                             # Py-spy (CPU 프로파일링, 스택 샘플)
npm install --save-dev clinic                  # Clinic.js (Node.js CPU/메모리/지연)
pip install prometheus-client                  # Prometheus 메트릭 내보내기
```

---

## 6. 보안 테스트·스캐닝 (20+)

### DAST (동적 분석)
```bash
pip install zaproxy                            # OWASP ZAP (동적 스캔, 프록시)
npm install --save-dev owasp-zap-sarif-plugin # ZAP SARIF 내보내기
pip install burp                               # Burp Suite Community (프록시·스캔)
pip install bandit                             # Bandit (Python 정적 보안 분석)
pip install semgrep                            # Semgrep (정적 SAST, 다언어)
```

### SAST (정적 분석)
```bash
pip install pylint                             # Pylint (Python 정적 분석)
npm install --save-dev eslint-plugin-security # ESLint 보안 플러그인
pip install safety                             # Safety (Python 의존성 취약점)
npm install --save-dev snyk                    # Snyk (의존성 + 코드 취약점)
npm install --save-dev retire                  # Retire.js (JS 라이브러리 취약점)
```

### 취약점 검색
```bash
pip install nuclei                             # Nuclei (템플릿 기반 취약점 스캔)
pip install sqlmap                             # SQLMap (SQL injection 테스트)
pip install nikto                              # Nikto (웹 서버 스캐너)
pip install wpscan                             # WPScan (WordPress 취약점)
pip install trivy                              # Trivy (컨테이너·의존성 스캔)
pip install grype                              # Grype (Syft 취약점 매칭)
```

### API 보안
```bash
npm install --save-dev 42crunch-cli            # 42Crunch API Security (OpenAPI)
pip install fuxploider                         # Fuxploider (FTP 취약점 검증)
pip install paramiko                           # Paramiko (SSH 자동화)
```

### 암호화·서명
```bash
pip install cryptography                       # Cryptography (암호 라이브러리)
pip install pycryptodome                       # PyCryptodome (AES, RSA, ECC)
pip install python-dotenv                      # .env 관리 (시크릿 보호)
npm install --save-dev dotenv                  # npm dotenv
```

---

## 7. 코드 품질·린팅 (25+)

### Python
```bash
pip install pylint                             # 포괄적 (정적 분석)
pip install flake8                             # 간단하지만 강력 (스타일 + 에러)
pip install black                              # 포맷팅 (opinionated, 일관성)
pip install isort                              # import 정렬
pip install mypy                               # 타입 체킹 (정적)
pip install pyright                            # Pyright (Microsoft, 더 빠른 타입)
pip install ruff                               # Ruff (Rust, 매우 빠른 린터)
pip install autopep8                           # PEP 8 자동 수정
pip install yapf                               # Google YAPF 포맷터
pip install pylama                             # 통합 린팅 (pylint+flake8+...)
pip install darglint                           # docstring 체크
pip install pydocstyle                         # PEP 257 docstring
pip install vulture                            # 미사용 코드 감지
```

### JavaScript/TypeScript
```bash
npm install --save-dev eslint                  # ESLint (JS 린터)
npm install --save-dev prettier                # Prettier (포맷터, opinionated)
npm install --save-dev typescript              # TypeScript (타입 체킹)
npm install --save-dev @typescript-eslint/eslint-plugin  # TS ESLint
npm install --save-dev stylelint               # CSS 린팅
npm install --save-dev htmlhint                # HTML 린팅
npm install --save-dev commitlint              # Commit 메시지 린팅
npm install --save-dev markdownlint            # Markdown 린팅
npm install --save-dev eslint-plugin-react    # React ESLint
npm install --save-dev eslint-plugin-vue      # Vue ESLint
npm install --save-dev eslint-plugin-next     # Next.js ESLint
```

### 여러 언어 (다언어)
```bash
pip install hadolint                           # Dockerfile 린팅
pip install shellcheck                         # Bash 스크립트 린팅
pip install actionlint                         # GitHub Actions 린팅
pip install yamllint                           # YAML 린팅
pip install json-schema-validator              # JSON 스키마 검증
```

### SonarQube (엔터프라이즈)
```bash
pip install sonar-python                       # SonarQube Python 플러그인
npm install --save-dev sonarqube-scanner       # SonarQube 스캐너
```

---

## 8. 뮤테이션 테스트 (5+)

### Python
```bash
pip install mutmut                             # 뮤테이션 테스트 (빠름)
pip install cosmic-ray                         # Cosmic Ray (분산 뮤테이션)
```

### JavaScript/TypeScript
```bash
npm install --save-dev stryker                 # Stryker (JS/TS/C#/.NET)
npm install --save-dev stryker-cli              # Stryker CLI
npm install --save-dev pitest                  # PIT (Java)
```

### 다중 언어
```bash
pip install mutagen                            # 다언어 뮤테이션 (고급)
```

---

## 9. 테스트 인프라·CI/CD (20+)

### CI/CD 플랫폼
```bash
# GitHub Actions (기본 제공)
# GitLab CI (기본 제공)
npm install --save-dev circleHonor              # CircleCI
npm install --save-dev travis-ci                # Travis CI (레거시)
pip install buildkite-agent                    # Buildkite
npm install --save-dev jenkins                 # Jenkins
```

### 모노레포·빌드 조율
```bash
npm install --save-dev nx                      # Nx (모노레포, 테스트 캐싱)
npm install --save-dev turbo                   # Turbo (모노레포, 빠른 캐싱)
npm install --save-dev lerna                   # Lerna (패키지 관리)
npm install --save-dev yarn workspaces         # Yarn (네이티브 workspaces)
npm install --save-dev pnpm                    # pnpm (빠른 설치, workspaces)
```

### 테스트 관리·리포팅
```bash
pip install allure-pytest                      # Allure (테스트 리포트, 히스토리)
npm install --save-dev allure-commandline      # Allure CLI
npm install --save-dev jest-html-reporters     # Jest HTML 리포트
npm install --save-dev mochawesome             # Mochawesome (Mocha 리포트)
pip install pytest-html                        # pytest HTML 리포트
pip install testrail-api                       # TestRail API (테스트 관리)
```

### 병렬 실행
```bash
npm install --save-dev jest-parallel-runner    # Jest 병렬 (더 빠름)
pip install pytest-xdist                       # pytest 분산 (여러 프로세스)
```

---

## 10. 테스트 데이터 관리·동적 의존성 (15+)

### 데이터 생성
```bash
pip install faker                              # Faker (이미 위에 있음)
pip install factory_boy                        # Factory Boy (이미 위에 있음)
npm install --save-dev fishery                 # Fishery (TS factory)
npm install --save-dev @faker-js/faker         # Faker JS
npm install --save-dev random-js               # Random.js (분포 기반)
pip install numpy                              # NumPy (수치 데이터)
pip install pandas                             # Pandas (데이터 조작)
```

### 컨테이너 기반 의존성
```bash
pip install testcontainers                     # Testcontainers (위에서 중복)
npm install --save-dev testcontainers          # Testcontainers JS
pip install docker                             # Docker Python API
npm install --save-dev docker                  # Docker JS API
```

### 서비스 시뮬레이션
```bash
pip install wiremock                           # WireMock (API 시뮬레이션)
npm install --save-dev json-server             # json-server (빠른 REST mock)
pip install localstack                         # LocalStack (AWS 에뮬레이션)
pip install moto                               # Moto (AWS 메모리 mock)
npm install --save-dev minio                   # MinIO (S3 호환, 메모리)
```

---

## 11. 시각적·스냅샷 테스트 (10+)

### 시각적 회귀
```bash
npm install --save-dev percy                   # Percy (시각적 회귀, SaaS)
npm install --save-dev chromatic               # Chromatic (Storybook 시각적)
npm install --save-dev backstopjs               # BackstopJS (로컬 CSS 회귀)
npm install --save-dev reg-suit                # reg-suit (회귀 리포팅)
npm install --save-dev jest-image-snapshot     # jest-image-snapshot
npm install --save-dev pixelmatch              # pixelmatch (이미지 비교)
```

### 스크린샷·스냅샷
```bash
npm install --save-dev jest-snapshot-serializer  # Snapshot (이미 위에)
npm install --save-dev @storybook/test-runner    # Storybook (이미 위에)
npm install --save-dev jest-html-reporters       # HTML 리포트 (이미 위에)
npm install --save-dev puppeteer-to-istanbul     # 스크린샷 커버리지
```

---

## 12. 접근성·성능 테스트 (12+)

### 접근성 (a11y)
```bash
npm install --save-dev axe-core                # axe-core (기본 엔진)
npm install --save-dev @axe-core/playwright    # axe + Playwright
npm install --save-dev jest-axe                # jest-axe
pip install python-axe                         # Python axe
npm install --save-dev pa11y                   # pa11y (CLI)
npm install --save-dev jest-a11y               # jest-a11y
npm install --save-dev cypress-axe             # cypress-axe (이미 위에)
npm install --save-dev lighthouse              # Lighthouse CLI
npm install --save-dev wave-api                # WAVE API (웹 접근성)
```

### 성능
```bash
npm install --save-dev lighthouse              # Lighthouse (성능+a11y)
npm install --save-dev web-vitals              # Web Vitals (LCP, FID, CLS)
npm install --save-dev speedcurve              # Speedcurve (성능 모니터링)
npm install --save-dev pagespeed-insights-api  # PageSpeed Insights API
```

---

## 13. 모니터링·관찰성 (10+)

### 테스트 메트릭·모니터링
```bash
pip install prometheus-client                  # Prometheus (이미 위에)
npm install --save-dev prom-client             # prom-client
pip install grafana-api                        # Grafana API
pip install datadog                            # Datadog (APM/모니터링)
npm install --save-dev dd-browser-sdk-rum      # Datadog RUM (브라우저)
pip install newrelic                           # New Relic (APM)
npm install --save-dev elastic-apm             # Elastic APM
pip install sentry-sdk                         # Sentry (에러 추적)
npm install --save-dev @sentry/browser         # Sentry (브라우저 에러)
```

---

## 요약·선택 가이드

| 용도 | 1순위 | 2순위 | 비고 |
|---|---|---|---|
| **단위 테스트 (Python)** | pytest | unittest | pytest 가 구조 자유도 높음 |
| **단위 테스트 (JS)** | Jest | Vitest | Vitest 가 더 빠름 (ESM) |
| **E2E (모든 브라우저)** | Playwright | Cypress | Playwright 가 교차 브라우저 |
| **API 테스트** | schemathesis | supertest | 자동화 수준 차이 |
| **성능 테스트** | k6 | locust | K6 가 CI-native |
| **보안 스캔** | semgrep | bandit | Semgrep 이 더 포괄적 |
| **린팅 (Python)** | ruff | pylint | Ruff 가 훨씬 빠름 |
| **린팅 (JS)** | ESLint | Prettier | 둘 다 필수 (lint + format) |
| **뮤테이션** | mutmut (Py) / Stryker (JS) | — | 커버리지 보완용 |
| **시각적 회귀** | Percy | BackstopJS | Percy 가 클라우드 기반 |
| **모니터링** | Prometheus | Datadog | 오픈소스 vs SaaS |

---

## 설치·통합 체크리스트

```bash
# Python
pip install pytest pytest-cov pytest-asyncio faker responses freezegun \
            coverage bandit semgrep hypothesis tox

# JavaScript
npm install --save-dev jest @testing-library/react supertest \
            @playwright/test cypress prettier eslint typescript

# CI/CD
# GitHub Actions (권장 — 무료, 기본 제공)
# K6 (성능) / Locust (부하) 중 선택
# Percy 또는 BackstopJS (시각적)
# Semgrep 또는 ZAP (보안)
```

---

## 참조

- **pytest 문서**: https://docs.pytest.org/
- **Jest 문서**: https://jestjs.io/
- **Playwright 문서**: https://playwright.dev/
- **K6 문서**: https://k6.io/docs/
- **OWASP**: https://owasp.org/
- **SonarQube**: https://www.sonarqube.org/
- **Storybook**: https://storybook.js.org/
- **Pact 문서**: https://pact.foundation/

---

## 프로젝트별 권장 조합 (orchestration_v1 예시)

### 백엔드 (Python + FastAPI/Django)
```text
Core: pytest, faker, responses, hypothesis
Quality: ruff, black, mypy, pylint, bandit
Perf: k6, locust
Security: semgrep, nuclei
CI: GitHub Actions + Allure
```

### 프론트엔드 (React/Vue + TypeScript)
```text
Core: Jest, @testing-library/*, Playwright
Quality: ESLint, Prettier, TypeScript
Visual: Percy
Perf: Lighthouse, web-vitals
CI: GitHub Actions
```

### 풀스택
```text
백엔드 + 프론트엔드 +
API: schemathesis, Pact (microservices)
E2E: Playwright (전체 흐름)
Monitoring: Prometheus + Grafana
```

---

**마지막 업데이트**: 2026-05-20 (180+ 도구, 13 카테고리)
