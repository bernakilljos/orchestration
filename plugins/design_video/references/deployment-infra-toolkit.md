# Deployment & Infrastructure Toolkit — 배포·CI/CD·모니터링·스케일링

> **목적**: 개발 → 배포 → 운영 전체 파이프라인 도구 총정리

---

## 1. 컨테이너 (Docker)

### Dockerfile 패턴
```dockerfile
# Python FastAPI
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Node.js (Multi-stage)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### docker-compose 패턴
```bash
docker compose up -d           # 시작
docker compose logs -f         # 로그
docker compose down            # 중지
docker compose exec app bash   # 컨테이너 진입
```

---

## 2. CI/CD

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: pytest --cov

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app && git pull && docker compose up -d --build
```

### 기타 CI/CD
| 도구 | 특장 | 비용 |
|------|------|------|
| **GitHub Actions** | GitHub 통합, 무료 티어 | 무료 2000분/월 |
| **GitLab CI** | 셀프호스팅 가능 | 무료 400분/월 |
| **Jenkins** | 오픈소스 표준 | 무료 (셀프호스팅) |
| **Dagger** | 컨테이너 기반 CI (로컬=클라우드) | 무료 |
| **Earthly** | Makefile + Docker 결합 | 무료 |

---

## 3. 클라우드 배포

### PaaS (가장 쉬움)
| 서비스 | 특장 | 무료 티어 |
|--------|------|----------|
| **Vercel** | Next.js/React 최적 | 무료 (hobby) |
| **Netlify** | 정적 사이트 + Functions | 무료 |
| **Railway** | Docker 원클릭 배포 | $5/월 크레딧 |
| **Render** | Docker/Web Service | 무료 (정적) |
| **Fly.io** | 글로벌 엣지 배포 | 무료 3 VM |
| **Cloudflare Workers** | 엣지 서버리스 | 무료 10만 req/일 |

### IaaS (직접 관리)
| 서비스 | 무료 | 특장 |
|--------|------|------|
| **Oracle Cloud Free** | 4 OCPU + 24GB RAM (영구 무료) | 가장 큰 무료 |
| **AWS Free Tier** | t2.micro 12개월 | 가장 넓은 서비스 |
| **GCP Free** | e2-micro (영구 무료) | AI/ML 강점 |
| **Azure Free** | B1S 12개월 | 엔터프라이즈 |
| **Hetzner** | CX22 €4.5/월 | 가성비 최강 (유럽) |
| **Vultr** | $2.5/월~ | 간단, 글로벌 |

### 서버리스
| 서비스 | 특장 |
|--------|------|
| **AWS Lambda** | 이벤트 기반 실행 |
| **Cloudflare Workers** | 엣지 실행 (V8) |
| **Supabase Edge Functions** | Deno 기반 |
| **Vercel Serverless Functions** | Next.js API Routes |

---

## 4. 리버스 프록시 / 로드 밸런서

| 도구 | 특장 | 설치 |
|------|------|------|
| **Nginx** | 표준 리버스 프록시 | `apt install nginx` |
| **Caddy** | 자동 HTTPS (Let's Encrypt) | `docker run -d -p 80:80 -p 443:443 caddy:2` |
| **Traefik** | Docker 네이티브 (자동 발견) | Docker |
| **HAProxy** | 고성능 로드 밸런서 | Docker |

### Caddy (자동 HTTPS)
```text
# Caddyfile
app.example.com {
    reverse_proxy localhost:8000
}

api.example.com {
    reverse_proxy localhost:3000
}
```

### Nginx
```nginx
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 5. 모니터링 / 관측성

### 메트릭
| 도구 | 특장 | Docker |
|------|------|--------|
| **Prometheus** | 메트릭 수집 표준 | `docker run -d -p 9090:9090 prom/prometheus:v2` |
| **Grafana** | 대시보드 시각화 | `docker run -d -p 3000:3000 grafana/grafana:10` |
| **Victoria Metrics** | Prometheus 호환 (경량) | Docker |

### 로깅
| 도구 | 특장 |
|------|------|
| **Loki** | Grafana 통합 로그 (경량) |
| **ELK Stack** | Elasticsearch + Logstash + Kibana |
| **Fluentd/Fluent Bit** | 로그 수집기 |

### 트레이싱
| 도구 | 특장 |
|------|------|
| **Jaeger** | 분산 트레이싱 (Uber) |
| **Zipkin** | 분산 트레이싱 (Twitter) |
| **OpenTelemetry** | 통합 관측 표준 (메트릭+로그+트레이스) |

### AI 관측
| 도구 | 특장 | 설치 |
|------|------|------|
| **LangFuse** | LLM 관측 (트레이싱+평가) | `pip install langfuse` |
| **Phoenix** | Arize AI 관측 | `pip install arize-phoenix` |
| **Langsmith** | LangChain 관측 | `pip install langsmith` |
| **Helicone** | LLM 프록시 (비용 추적) | 클라우드 |

### Python 모니터링
```bash
pip install prometheus-client  # Prometheus 메트릭 노출
pip install opentelemetry-api  # OpenTelemetry
pip install sentry-sdk         # 에러 트래킹
pip install structlog          # 구조화 로깅
pip install loguru             # 간편 로깅
```

---

## 6. DNS / 도메인 / CDN

| 서비스 | 특장 | 비용 |
|--------|------|------|
| **Cloudflare** | DNS + CDN + DDoS 방어 + Workers | 무료 |
| **AWS CloudFront** | CDN (S3 연동) | 종량제 |
| **Bunny CDN** | 저렴한 CDN ($1/TB) | $1/TB |
| **Fastly** | 엣지 컴퓨팅 CDN | 종량제 |

---

## 7. 시크릿 / 설정 관리

| 도구 | 특장 | 설치 |
|------|------|------|
| **dotenv** | .env 파일 | `pip install python-dotenv` |
| **Vault** | HashiCorp 시크릿 관리 | Docker |
| **AWS Secrets Manager** | 클라우드 시크릿 | boto3 |
| **Doppler** | 시크릿 동기화 (팀) | CLI |
| **SOPS** | 암호화된 시크릿 파일 | CLI |
| **Infisical** | 오픈소스 시크릿 관리 | Docker |

---

## 8. IaC (Infrastructure as Code)

| 도구 | 언어 | 특장 |
|------|------|------|
| **Terraform** | HCL | 클라우드 인프라 표준 |
| **Pulumi** | Python/TypeScript/Go | 일반 프로그래밍 언어 |
| **Ansible** | YAML | 서버 설정 관리 |
| **CDK** | TypeScript/Python | AWS 전용 IaC |

```bash
pip install pulumi            # Pulumi Python
pip install ansible           # Ansible
```

---

## 9. 쿠버네티스 (K8s)

### 로컬 K8s
| 도구 | 특장 |
|------|------|
| **Docker Desktop K8s** | 가장 간단 |
| **Minikube** | 단일 노드 K8s |
| **K3s** | 경량 K8s (IoT/Edge) |
| **Kind** | Docker-in-Docker K8s |

### K8s 도구
```bash
pip install kubernetes        # Python K8s 클라이언트
# kubectl, helm, kustomize — CLI
```

### 관리형 K8s
| 서비스 | 클라우드 |
|--------|----------|
| **EKS** | AWS |
| **GKE** | GCP |
| **AKS** | Azure |
| **OKE** | Oracle Cloud |

---

## 추천 조합

### 1인 개발자 (최소 비용)
```text
SQLite + Redis + Caddy + Oracle Free Tier + GitHub Actions
```

### 스타트업 (중규모)
```text
PostgreSQL + Redis + Meilisearch + Docker Compose + Render/Railway + Sentry + Grafana
```

### 엔터프라이즈 (대규모)
```text
PostgreSQL (RDS) + Redis Cluster + Elasticsearch + Kafka + K8s (EKS) + Prometheus + Grafana + Vault + Terraform
```

### AI 서비스
```text
PostgreSQL + ChromaDB + Redis + Celery + FastAPI + Vercel (프론트) + LangFuse + Sentry
```
