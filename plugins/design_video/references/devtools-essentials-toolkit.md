# DevTools Essentials — 개발자 필수 도구 총정리 (2026)

> **목적**: 개발 환경·워크플로우·DevOps·관리 도구 중 우리 킷에 없던 것 보강
> **출처**: 2026 developer toolkit 웹 조사 + awesome-list 크로스체크

---

## 1. DB GUI / 관리 도구

| 도구 | 특장 | 비용 |
|------|------|------|
| **DBeaver** | 50+ DB 지원 (PostgreSQL·MySQL·MongoDB) | 무료 (CE) |
| **TablePlus** | 네이티브 DB 클라이언트 (빠름, 깔끔) | $89 (Trial 무료) |
| **DataGrip** | JetBrains DB IDE | $99/년 |
| **Beekeeper Studio** | 오픈소스 SQL 에디터 | 무료 (CE) |
| **pgAdmin** | PostgreSQL 전용 관리 | 무료 |
| **MongoDB Compass** | MongoDB GUI | 무료 |
| **Redis Insight** | Redis GUI (공식) | 무료 |
| **Prisma Studio** | Prisma ORM 시각 에디터 | 무료 |

---

## 2. 터미널 / 쉘

| 도구 | 특장 | 비용 |
|------|------|------|
| **Warp** | AI 터미널 (자동완성, 블록) | 무료 |
| **iTerm2** | macOS 터미널 표준 | 무료 |
| **Windows Terminal** | Windows 모던 터미널 | 무료 |
| **Alacritty** | GPU 가속 터미널 (최빠름) | 무료 |
| **Ghostty** | 모던 터미널 (Zig 기반) | 무료 |
| **Starship** | 크로스쉘 프롬프트 (빠름, 커스텀) | 무료 |
| **Oh My Zsh** | Zsh 플러그인 매니저 | 무료 |
| **Fig/Amazon Q** | 터미널 자동완성 | 무료 |
| **tmux** | 터미널 멀티플렉서 | 무료 |
| **zoxide** | 스마트 cd (자주 가는 폴더 학습) | 무료 |
| **fzf** | 퍼지 파인더 (파일, 히스토리 검색) | 무료 |
| **bat** | cat 대체 (구문 하이라이트) | 무료 |
| **eza** | ls 대체 (아이콘, 컬러) | 무료 |
| **ripgrep** | grep 대체 (10x 빠름) | 무료 |
| **delta** | git diff 뷰어 (구문 하이라이트) | 무료 |
| **lazygit** | TUI Git 클라이언트 | 무료 |
| **lazydocker** | TUI Docker 관리 | 무료 |

---

## 3. 프로젝트 관리

| 도구 | 특장 | 무료 |
|------|------|------|
| **Linear** | 개발팀 이슈 트래커 (빠름) | ✅ (250 이슈) |
| **Jira** | 엔터프라이즈 프로젝트 관리 | ✅ (10명) |
| **Notion** | 위키 + 프로젝트 + DB | ✅ |
| **Trello** | 칸반 보드 | ✅ |
| **GitHub Projects** | GitHub 통합 프로젝트 | ✅ |
| **Plane** | 오픈소스 Jira 대안 | ✅ |
| **Taiga** | 오픈소스 애자일 관리 | ✅ |

---

## 4. MLOps / 실험 관리

| 도구 | 특장 | 설치 |
|------|------|------|
| **MLflow** | 실험 추적 + 모델 레지스트리 표준 | `pip install mlflow` |
| **Weights & Biases** | 실험 시각화 (대시보드) | `pip install wandb` |
| **DVC** | 데이터 버전 관리 (Git for Data) | `pip install dvc` |
| **Kubeflow** | K8s 위 ML 파이프라인 | Helm |
| **BentoML** | 모델 서빙 + 배포 | `pip install bentoml` |
| **Ray** | 분산 ML 프레임워크 | `pip install ray` |
| **ClearML** | 오픈소스 MLOps | `pip install clearml` |
| **Aim** | 실험 추적 (MLflow 대안) | `pip install aim` |

```python
# MLflow 실험 추적
import mlflow
mlflow.set_experiment("my-experiment")
with mlflow.start_run():
    mlflow.log_param("lr", 0.01)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.sklearn.log_model(model, "model")
```

---

## 5. 에러 트래킹 / 모니터링

| 도구 | 특장 | 무료 |
|------|------|------|
| **Sentry** | 에러 트래킹 표준 (AI 자동 분석) | ✅ (5k 이벤트/월) |
| **BugSnag** | 에러 모니터링 | ✅ (7500 이벤트/월) |
| **LogRocket** | 세션 리플레이 + 에러 | ✅ (1k 세션/월) |
| **Highlight.io** | 오픈소스 세션 리플레이 | ✅ |
| **Datadog** | APM + 로그 + 메트릭 통합 | ✅ (제한적) |
| **New Relic** | APM 표준 | ✅ (100GB/월) |
| **Uptime Kuma** | 오픈소스 업타임 모니터 | ✅ |
| **Better Stack** | 업타임 + 로그 | ✅ |

```python
pip install sentry-sdk
import sentry_sdk
sentry_sdk.init(dsn="https://xxx@sentry.io/xxx", traces_sample_rate=1.0)
```

---

## 6. 노코드 / 로우코드 / 자동화

| 도구 | 특장 | 무료 |
|------|------|------|
| **n8n** | 오픈소스 워크플로우 자동화 (Zapier 대안) | ✅ (셀프호스팅) |
| **Zapier** | 7000+ 앱 연결 | ✅ (100 태스크/월) |
| **Make (Integromat)** | 비주얼 자동화 | ✅ (1000 ops/월) |
| **Retool** | 내부 도구 빌더 | ✅ (5 사용자) |
| **Appsmith** | 오픈소스 내부 도구 | ✅ |
| **Tooljet** | 오픈소스 로우코드 | ✅ |
| **Budibase** | 오픈소스 앱 빌더 | ✅ |
| **Directus** | 오픈소스 Headless CMS + API | ✅ |
| **NocoDB** | 오픈소스 Airtable 대안 | ✅ |
| **Baserow** | 오픈소스 Airtable 대안 | ✅ |

---

## 7. CMS (콘텐츠 관리 시스템)

| 도구 | 특장 | 무료 |
|------|------|------|
| **Strapi** | 오픈소스 Headless CMS (Node.js) | ✅ |
| **Sanity** | 구조화 콘텐츠 (실시간 협업) | ✅ (무료 티어) |
| **Contentful** | 엔터프라이즈 Headless CMS | ✅ (무료 티어) |
| **Payload** | 오픈소스 CMS + 앱 프레임워크 | ✅ |
| **Ghost** | 퍼블리싱 플랫폼 (블로그) | ✅ (셀프호스팅) |
| **WordPress** | 세계 1위 CMS | ✅ |
| **KeystoneJS** | 오픈소스 Headless CMS (GraphQL) | ✅ |
| **Decap CMS** | Git 기반 CMS (정적 사이트) | ✅ |

---

## 8. 테스트 (E2E / 유닛 / 성능)

### JavaScript/TypeScript
| 도구 | 특장 | 설치 |
|------|------|------|
| **Vitest** | Vite 네이티브 테스트 (Jest 대체) | `npm install vitest` |
| **Playwright** | E2E 테스트 (크로스 브라우저) | `npm install @playwright/test` |
| **Cypress** | E2E 테스트 (시각적, DX 최고) | `npm install cypress` |
| **Jest** | 유닛 테스트 표준 | `npm install jest` |
| **Testing Library** | 컴포넌트 테스트 | `npm install @testing-library/react` |
| **Storybook** | UI 컴포넌트 문서화 + 테스트 | `npm install storybook` |
| **MSW** | API 모킹 (Service Worker) | `npm install msw` |
| **k6** | 부하 테스트 (Grafana) | CLI |

### Python
```bash
pip install pytest pytest-cov hypothesis faker  # 이미 카탈로그에 있음
pip install locust            # 부하 테스트 (Python)
pip install robot             # Robot Framework
```

---

## 9. 문서 도구

| 도구 | 특장 | 무료 |
|------|------|------|
| **Docusaurus** | React 문서 사이트 (Meta) | ✅ |
| **Mintlify** | AI 문서 (Stripe 스타일) | ✅ (무료 티어) |
| **GitBook** | 팀 문서 | ✅ (개인) |
| **Nextra** | Next.js 문서 | ✅ |
| **VitePress** | Vite 정적 문서 (Vue) | ✅ |
| **Starlight** | Astro 문서 | ✅ |
| **Readme** | API 문서 (인터랙티브) | ✅ (무료 티어) |
| **Swagger/OpenAPI** | API 스펙 문서 | ✅ |
| **Redoc** | OpenAPI 문서 렌더링 | ✅ |

---

## 10. 디자인 → 코드 (AI)

| 도구 | 특장 | 무료 |
|------|------|------|
| **v0.dev** | 프롬프트→React UI (Vercel) | ✅ |
| **Bolt.new** | 프롬프트→풀스택 앱 | ✅ |
| **Lovable** | 프롬프트→앱 (GPT Engineer 후속) | ✅ |
| **Screenshot-to-Code** | 스크린샷→HTML/React | ✅ (오픈소스) |
| **Figma→Code** | Figma 디자인→코드 | Figma 플러그인 |
| **Vercel AI SDK** | AI 앱 빌드 프레임워크 | ✅ |
| **Langbase** | AI 파이프 빌더 | ✅ |

---

## 11. 패키지 관리 / 빌드

| 도구 | 특장 | 설치 |
|------|------|------|
| **pnpm** | 빠른 Node 패키지 매니저 (디스크 절약) | `npm install -g pnpm` |
| **Bun** | JS 런타임 + 패키지 매니저 + 번들러 (올인원) | bun.sh |
| **Turborepo** | 모노레포 빌드 시스템 (Vercel) | `npm install turbo` |
| **Nx** | 모노레포 빌드 (Nrwl) | `npm install nx` |
| **Vite** | 프론트엔드 빌드 (최빠름) | `npm install vite` |
| **esbuild** | Go 기반 JS 번들러 (100x 빠름) | `npm install esbuild` |
| **SWC** | Rust 기반 JS 컴파일러 | `npm install @swc/core` |
| **uv** | Rust 기반 Python 패키지 매니저 (100x 빠름) | `pip install uv` |
| **Rye** | Python 프로젝트 매니저 | rye.astral.sh |
| **Poetry** | Python 의존성 관리 | `pip install poetry` |

---

## 12. 린터 / 포매터

| 도구 | 언어 | 설치 |
|------|------|------|
| **ESLint** | JS/TS 린터 | `npm install eslint` |
| **Prettier** | 코드 포매터 (다국어) | `npm install prettier` |
| **Biome** | ESLint+Prettier 통합 (Rust, 빠름) | `npm install @biomejs/biome` |
| **Ruff** | Python 린터+포매터 (Rust, 100x 빠름) | `pip install ruff` |
| **Black** | Python 포매터 | `pip install black` |
| **mypy** | Python 타입 체크 | `pip install mypy` |
| **Stylelint** | CSS 린터 | `npm install stylelint` |
| **ShellCheck** | Bash 린터 | apt/brew |
| **hadolint** | Dockerfile 린터 | Docker |
| **actionlint** | GitHub Actions 린터 | CLI |
| **commitlint** | 커밋 메시지 린터 | `npm install @commitlint/cli` |

---

## 13. 시크릿 / 환경 관리

| 도구 | 특장 | 무료 |
|------|------|------|
| **Doppler** | 시크릿 동기화 (팀) | ✅ (5명) |
| **Infisical** | 오픈소스 시크릿 관리 | ✅ |
| **1Password CLI** | 개발자 시크릿 (SSH, API 키) | $3/월 |
| **direnv** | 디렉토리별 환경변수 자동 로드 | 무료 |
| **dotenvx** | dotenv 차세대 (암호화 지원) | 무료 |

---

## 14. API 개발 / 테스트

| 도구 | 특장 | 무료 |
|------|------|------|
| **Bruno** | 오픈소스 API 클라이언트 (Git 친화) | ✅ |
| **Hoppscotch** | 오픈소스 Postman 대안 (웹) | ✅ |
| **Insomnia** | API 클라이언트 (Kong) | ✅ |
| **Postman** | API 개발 표준 | ✅ (무료 티어) |
| **httpie** | CLI HTTP 클라이언트 (Python) | ✅ |
| **Thunder Client** | VS Code API 클라이언트 | ✅ |

---

## 15. 백엔드 서비스 (BaaS)

| 도구 | 특장 | 무료 |
|------|------|------|
| **Supabase** | 오픈소스 Firebase 대안 (PostgreSQL) | ✅ (500MB) |
| **Firebase** | Google BaaS (인증+DB+스토리지+호스팅) | ✅ |
| **Appwrite** | 오픈소스 BaaS | ✅ |
| **PocketBase** | Go 싱글바이너리 BaaS | ✅ |
| **Convex** | 리액티브 BaaS (실시간) | ✅ |
| **Neon** | 서버리스 PostgreSQL | ✅ (0.5GB) |
| **Turso** | 서버리스 SQLite (엣지) | ✅ (9GB) |
| **Upstash** | 서버리스 Redis + Kafka | ✅ |

---

## 추천 조합

### 솔로 풀스택
```text
Supabase + Next.js + Vercel + Sentry + Bruno + Ruff + Biome
```

### 스타트업 팀
```text
Linear + GitHub Actions + Docker + Supabase + n8n + Sentry + Doppler
```

### AI 서비스
```text
MLflow + W&B + FastAPI + Supabase + Sentry + DVC + Claude API
```

### 문서 중심
```text
Docusaurus + Mintlify + Swagger + Storybook + GitHub Pages
```

---

## 16. Dev Containers (개발 환경 재현)

| 도구 | 특장 | 설치 |
|------|------|------|
| **Dev Containers** | Docker 기반 개발 환경 (VS Code 통합) | `.devcontainer/devcontainer.json` |
| **Gitpod** | 클라우드 개발 환경 | gitpod.io |
| **GitHub Codespaces** | GitHub 클라우드 IDE | github.com |
| **Coder** | 셀프호스팅 개발 환경 | Docker |
| **Nix** | 재현 가능한 빌드 + 개발 환경 | nixos.org |
| **devenv** | Nix 기반 개발 환경 (간편) | devenv.sh |
| **mise** | 다국어 런타임 매니저 (asdf 대체) | mise.jdx.dev |

```json
// .devcontainer/devcontainer.json
{
  "name": "Python Dev",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "pip install -r requirements.txt",
  "customizations": { "vscode": { "extensions": ["ms-python.python"] } }
}
```

---

## 17. Feature Flags / 점진 배포

| 도구 | 특장 | 무료 |
|------|------|------|
| **Unleash** | 오픈소스 피처 플래그 | ✅ (셀프호스팅) |
| **GrowthBook** | 오픈소스 A/B 테스트 + 피처 플래그 | ✅ |
| **LaunchDarkly** | 엔터프라이즈 피처 플래그 | 유료 |
| **Flipt** | 오픈소스 (Go, 경량) | ✅ |
| **PostHog** | 분석 + 피처 플래그 + 세션 리플레이 | ✅ (무료 티어) |
| **Flagsmith** | 오픈소스 피처 플래그 | ✅ |

---

## 18. Workflow / Orchestration

| 도구 | 특장 | 설치 |
|------|------|------|
| **Temporal** | 내구성 워크플로우 엔진 (마이크로서비스) | Docker |
| **Inngest** | 이벤트 기반 함수 (서버리스) | `npm install inngest` |
| **Trigger.dev** | 백그라운드 작업 (서버리스) | `npm install @trigger.dev/sdk` |
| **Hatchet** | 분산 태스크 큐 (Go) | Docker |
| **Windmill** | 오픈소스 워크플로우 (Retool+Temporal) | Docker |

---

## 19. Cost / Budget Monitoring

| 도구 | 특장 | 무료 |
|------|------|------|
| **Infracost** | Terraform 비용 예측 | ✅ |
| **Vantage** | 클라우드 비용 분석 | ✅ (무료 티어) |
| **OpenCost** | K8s 비용 모니터링 (오픈소스) | ✅ |
| **Helicone** | LLM API 비용 추적 | ✅ (무료 티어) |
| **LiteLLM** | LLM 프록시 + 비용 추적 | `pip install litellm` |
| **portkey** | AI Gateway (비용+캐싱+로깅) | ✅ (무료 티어) |

---

## 20. Chaos Engineering / 안정성

| 도구 | 특장 | 설치 |
|------|------|------|
| **Chaos Monkey** | Netflix 카오스 엔진 | GitHub |
| **Litmus** | K8s 카오스 테스트 | Docker |
| **Gremlin** | 카오스 SaaS | 유료 |
| **Toxiproxy** | 네트워크 장애 시뮬레이션 | `go install` |
| **k6** | 부하 테스트 (Grafana) | ✅ |
| **Grafana k6** | 분산 부하 테스트 | ✅ |

---

## 21. Observability (관측성 심화)

| 도구 | 특장 | 설치 |
|------|------|------|
| **OpenTelemetry** | 메트릭+로그+트레이스 통합 표준 | `pip install opentelemetry-api` |
| **SigNoz** | 오픈소스 Datadog 대안 | Docker |
| **Grafana Stack** | Prometheus+Loki+Tempo+Grafana | Docker |
| **Axiom** | 서버리스 로그+트레이스 | ✅ (무료 티어) |
| **Baselime** | 서버리스 관측 | ✅ |

```python
# OpenTelemetry — Python 자동 계측
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
opentelemetry-instrument python app.py
```
