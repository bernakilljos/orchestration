# API Gateway & Microservices Toolkit

> **목적**: API 게이트웨이·마이크로서비스 관련 80+ 공통 도구 레퍼런스
> **적용**: API 라우팅·인증·레이트 리미팅·서비스 디스커버리 등
> **최신**: 2026-05-20

---

## 1. API 게이트웨이 (API Gateway)

### Kong
- **용도**: 오픈소스 API 게이트웨이, 마이크로서비스 관리
- **특징**: 플러그인 기반, 높은 확장성
- **설치**:
  ```bash
  docker run -d --name kong-database \
    -e "POSTGRES_USER=kong" \
    -e "POSTGRES_DB=kong" \
    postgres:latest
  
  docker run -d --name kong \
    -e "KONG_DATABASE=postgres" \
    -e "KONG_PG_HOST=kong-database" \
    -p 8000:8000 -p 8443:8443 -p 8001:8001 \
    kong:latest
  ```
- **설정 예시**:
  ```bash
  # Service 추가
  curl -i -X POST http://localhost:8001/services/ \
    -d "name=my-service" \
    -d "url=http://backend:3000"
  
  # Route 추가
  curl -i -X POST http://localhost:8001/services/my-service/routes \
    -d "hosts[]=example.com" \
    -d "paths[]=/api"
  ```

### Tyk
- **용도**: 상용 API 게이트웨이 (오픈소스 버전도 있음)
- **특징**: API 분석, 사용량 제한, 인증
- **설치**:
  ```bash
  docker run -d \
    -p 8080:8080 \
    -e TYK_GW_STORAGE_CONNECTIONSTRING=localhost:6379 \
    tykio/tyk-gateway:latest
  ```

### APISIX (Apache)
- **용도**: 클라우드 네이티브 API 게이트웨이
- **특징**: 고성능, 동적 업데이트, Lua 플러그인
- **설치**:
  ```bash
  docker run -d \
    -p 9080:9080 \
    -p 9443:9443 \
    apache/apisix:latest
  ```

### KrakenD
- **용도**: 경량 API 게이트웨이, API 컴포저
- **특징**: 설정 기반, 백엔드 조합
- **설치**:
  ```bash
  docker run -d -p 8080:8080 \
    -v $(pwd)/krakend.json:/etc/krakend/krakend.json \
    krakend/krakend:latest
  ```

### Traefik
- **용도**: 역프록시, 마이크로서비스용 라우터
- **특징**: Docker/Kubernetes 자동 통합
- **설치**:
  ```bash
  docker run -d \
    -p 80:80 -p 8080:8080 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    traefik:latest --api --entrypoints.web.address=:80
  ```

### AWS API Gateway
- **용도**: AWS 관리형 API 게이트웨이
- **특징**: Lambda 통합, IAM 인증
- **설정** (AWS CLI):
  ```bash
  aws apigateway create-rest-api \
    --name "my-api" \
    --description "My API"
  ```

### Azure API Management
- **용도**: Azure 관리형 API 게이트웨이
- **특징**: API 버전 관리, 정책 엔진
- **설정** (Azure CLI):
  ```bash
  az apim create --name myapim \
    --resource-group mygroup \
    --publisher-email admin@example.com \
    --publisher-name "My Publisher"
  ```

---

## 2. 서비스 디스커버리 (Service Discovery)

### Consul (HashiCorp)
- **용도**: 서비스 디스커버리, 분산 설정 관리
- **특징**: 헬스 체크, DNS 인터페이스
- **설치**:
  ```bash
  docker run -d --name consul \
    -p 8500:8500 -p 8600:8600/udp \
    consul:latest agent -server -ui \
    -bootstrap-expect=1 -client=0.0.0.0
  ```
- **서비스 등록**:
  ```bash
  curl -X PUT http://localhost:8500/v1/agent/service/register \
    -d '{
      "ID": "service-1",
      "Name": "my-service",
      "Port": 3000,
      "Check": {
        "HTTP": "http://localhost:3000/health",
        "Interval": "10s"
      }
    }'
  ```

### Eureka (Netflix)
- **용도**: Spring Cloud 기반 서비스 디스커버리
- **특징**: Java/Spring Boot 통합
- **설정** (Spring Boot):
  ```yaml
  spring:
    application:
      name: my-service
    eureka:
      client:
        serviceUrl:
          defaultZone: http://localhost:8761/eureka/
  ```

### Nacos (Alibaba)
- **용도**: 동적 서비스 디스커버리, 설정 관리
- **특징**: DNS/HTTP 기반 디스커버리
- **설치**:
  ```bash
  docker run -d --name nacos \
    -e MODE=standalone \
    -p 8848:8848 \
    nacos/nacos-server:latest
  ```

### etcd
- **용도**: 분산 키-값 저장소, 서비스 레지스트리
- **특징**: 일관성, Kubernetes 사용
- **설치**:
  ```bash
  docker run -d --name etcd \
    -p 2379:2379 \
    quay.io/coreos/etcd:latest
  ```

### Zookeeper
- **용도**: 분산 조정, 서비스 등록
- **특징**: Kafka, HBase 등과 통합
- **설치**:
  ```bash
  docker run -d --name zookeeper \
    -p 2181:2181 \
    zookeeper:latest
  ```

---

## 3. 로드 밸런싱 (Load Balancing)

### Nginx
- **용도**: 고성능 웹 서버, 로드 밸런서
- **설치**:
  ```bash
  sudo apt-get install nginx
  # macOS: brew install nginx
  ```
- **설정 예시** (`/etc/nginx/nginx.conf`):
  ```nginx
  upstream backend {
    server backend1.example.com weight=5;
    server backend2.example.com weight=5;
  }
  
  server {
    listen 80;
    location / {
      proxy_pass http://backend;
    }
  }
  ```

### HAProxy
- **용도**: TCP/HTTP 로드 밸런싱
- **특징**: 높은 성능, 정교한 라우팅
- **설치**:
  ```bash
  sudo apt-get install haproxy
  ```
- **설정**:
  ```text
  global
    maxconn 100000
  
  frontend web
    bind *:80
    default_backend servers
  
  backend servers
    server srv1 192.168.1.10:8000
    server srv2 192.168.1.11:8000
  ```

### Envoy
- **용도**: L3/L4/L7 프록시, 서비스 메시 통합
- **특징**: 고급 라우팅, 관찰성
- **설치**:
  ```bash
  docker run -d -p 10000:10000 \
    envoyproxy/envoy:v1.27-latest
  ```

### Traefik (로드 밸런싱)
- 위 "API 게이트웨이" 섹션 참조

### Caddy
- **용도**: 간단한 웹 서버, 자동 HTTPS
- **설치**:
  ```bash
  sudo apt-get install caddy
  ```
- **Caddyfile**:
  ```text
  example.com {
    reverse_proxy localhost:3000 localhost:3001
  }
  ```

---

## 4. 레이트 리미팅 (Rate Limiting)

### Redis + Lua (일반적)
- **용도**: 분산 레이트 리미팅
- **알고리즘**: Token bucket, Sliding window
- **예시** (Python):
  ```python
  import redis
  import time
  
  r = redis.Redis()
  
  def rate_limit(user_id, limit=100, window=60):
      key = f"rate_limit:{user_id}"
      current = r.incr(key)
      if current == 1:
          r.expire(key, window)
      return current <= limit
  ```

### express-rate-limit (Node.js)
- **설치**:
  ```bash
  npm install express-rate-limit
  ```
- **사용**:
  ```javascript
  const rateLimit = require('express-rate-limit');
  
  const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15분
    max: 100 // 최대 100 요청
  });
  
  app.use('/api/', limiter);
  ```

### flask-limiter (Python)
- **설치**:
  ```bash
  pip install Flask-Limiter
  ```
- **사용**:
  ```python
  from flask_limiter import Limiter
  from flask_limiter.util import get_remote_address
  
  limiter = Limiter(app, key_func=get_remote_address)
  
  @app.route('/api/data')
  @limiter.limit("100 per hour")
  def get_data():
      return {"data": "..."}
  ```

### Bucket4j (Java)
- **설치** (Maven):
  ```xml
  <dependency>
    <groupId>com.github.vladimir-bukhtoyarov</groupId>
    <artifactId>bucket4j-core</artifactId>
    <version>7.6.0</version>
  </dependency>
  ```

---

## 5. 인증/인가 (Authentication & Authorization)

### OAuth2 Proxy
- **용도**: OAuth2 프론트엔드 프록시
- **설치**:
  ```bash
  docker run -d \
    -p 4180:4180 \
    -e OAUTH2_PROXY_CLIENT_ID=xxx \
    -e OAUTH2_PROXY_CLIENT_SECRET=yyy \
    -e OAUTH2_PROXY_COOKIE_SECRET=zzz \
    oauth2-proxy/oauth2-proxy:latest
  ```

### Keycloak
- **용도**: 오픈소스 ID 제공자, SSO
- **설치**:
  ```bash
  docker run -d --name keycloak \
    -e KEYCLOAK_ADMIN=admin \
    -e KEYCLOAK_ADMIN_PASSWORD=change_me \
    -p 8080:8080 \
    quay.io/keycloak/keycloak:latest \
    start-dev
  ```

### OPA (Open Policy Agent)
- **용도**: 정책 기반 접근 제어 (ABAC/RBAC)
- **설치**:
  ```bash
  docker run -d -p 8181:8181 openpolicyagent/opa:latest
  ```
- **정책 예시**:
  ```rego
  package api.authz
  
  allow {
    input.user.role == "admin"
  }
  ```

### Casbin
- **용도**: 접근 제어 라이브러리 (Go, Node.js, Python)
- **설치** (Python):
  ```bash
  pip install casbin
  ```

### JWT (JSON Web Tokens)
- **용도**: 무상태 인증
- **라이브러리**:
  - Node.js: `jsonwebtoken`
  - Python: `PyJWT`
  - Java: `jjwt`
- **예시** (Node.js):
  ```javascript
  const jwt = require('jsonwebtoken');
  
  const token = jwt.sign(
    { user_id: 123 },
    'secret_key',
    { expiresIn: '1h' }
  );
  
  const verified = jwt.verify(token, 'secret_key');
  ```

---

## 6. API 버전닝 (API Versioning)

### URL Versioning
```text
GET /api/v1/users    # v1
GET /api/v2/users    # v2
```

### Header Versioning
```text
GET /api/users
Accept: application/vnd.company.v1+json
```

### MediaType Versioning
```text
Content-Type: application/vnd.company.v1+json
```

### 마이그레이션 전략
```bash
# 1. v1 지원 중단 공지
# 2. deprecation 헤더 추가
curl -i https://api.example.com/api/v1/users
# 응답: Deprecation: true
#       Sunset: Sun, 31 Dec 2026 23:59:59 GMT

# 3. 일정 후 v1 서버 종료
```

---

## 7. gRPC

### Protocol Buffers (protobuf)
- **설치**:
  ```bash
  sudo apt-get install protobuf-compiler
  # macOS: brew install protobuf
  ```
- **정의 예시** (`user.proto`):
  ```protobuf
  syntax = "proto3";
  
  package user;
  
  message User {
    int32 id = 1;
    string name = 2;
    string email = 3;
  }
  
  service UserService {
    rpc GetUser (UserId) returns (User);
  }
  ```

### grpc-go
- **설치**:
  ```bash
  go get -u google.golang.org/grpc
  go install github.com/grpc/grpc-go/cmd/protoc-gen-go-grpc@latest
  ```

### grpc-python
- **설치**:
  ```bash
  pip install grpcio grpcio-tools
  ```
- **컴파일**:
  ```bash
  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto
  ```

### grpc-node
- **설치**:
  ```bash
  npm install @grpc/grpc-js @grpc/proto-loader
  ```

### Connect (Buf)
- **용도**: gRPC + HTTP/1.1 호환
- **설치**:
  ```bash
  npm install @connectrpc/connect
  ```

---

## 8. GraphQL

### Apollo Server
- **설치**:
  ```bash
  npm install apollo-server
  ```
- **예시**:
  ```javascript
  const { ApolloServer, gql } = require('apollo-server');
  
  const typeDefs = gql`
    type Query {
      user(id: Int!): User
    }
    type User {
      id: Int!
      name: String!
    }
  `;
  
  const resolvers = {
    Query: {
      user: (_, { id }) => ({ id, name: 'John' })
    }
  };
  
  const server = new ApolloServer({ typeDefs, resolvers });
  server.listen();
  ```

### Hasura
- **용도**: 자동 GraphQL API 생성 (DB 기반)
- **설치**:
  ```bash
  docker run -d -p 8080:8080 \
    -e HASURA_GRAPHQL_DATABASE_URL=postgresql://... \
    hasura/graphql-engine:latest
  ```

### PostGraphile
- **용도**: PostgreSQL → GraphQL
- **설치**:
  ```bash
  npm install postgraphile
  npx postgraphile -c postgresql://user:pass@localhost/db
  ```

### Strawberry (Python)
- **설치**:
  ```bash
  pip install strawberry-graphql
  ```
- **예시**:
  ```python
  import strawberry
  
  @strawberry.type
  class User:
    id: int
    name: str
  
  @strawberry.type
  class Query:
    @strawberry.field
    def user(self, id: int) -> User:
      return User(id=id, name="John")
  ```

### graphql-yoga
- **설치**:
  ```bash
  npm install graphql-yoga
  ```

---

## 9. API 모니터링 (API Monitoring)

### Moesif
- **용도**: API 분석, 실시간 모니터링 (SaaS)
- **가격**: 시작 $250/월
- **설정**:
  ```javascript
  const moesifMiddleware = require('moesif-nodejs');
  app.use(moesifMiddleware.init({
    applicationId: '$MOESIF_ID'
  }));
  ```

### ReadyAPI
- **용도**: API 테스트, 모니터링 (SmartBear)
- **가격**: 상용, 연간 $829

### Runscope
- **용도**: API 모니터링, 부하 테스트 (SaaS)
- **가격**: 시작 무료

### Assertible
- **용도**: API 테스트 자동화
- **가격**: 시작 $29/월

---

## 10. API 문서 (API Documentation)

### Swagger/OpenAPI
- **설정 예시** (`openapi.yaml`):
  ```yaml
  openapi: 3.0.0
  info:
    title: My API
    version: 1.0.0
  paths:
    /users:
      get:
        summary: Get all users
        responses:
          200:
            description: Success
  ```
- **생성 도구**: Swagger Editor

### Redoc
- **용도**: 아름다운 API 문서 생성
- **설치**:
  ```bash
  npm install -g redoc-cli
  redoc-cli build openapi.yaml -o docs.html
  ```

### Stoplight
- **용도**: API 설계, 문서화 (시각 에디터)
- **사용**: https://stoplight.io

### Postman
- **용도**: API 테스트, 문서 생성
- **다운로드**: https://www.postman.com
- **문서 공유**: Postman Workspace

### Hoppscotch
- **용도**: 오픈소스 API 클라이언트
- **설치**:
  ```bash
  docker run -d -p 3000:3000 hoppscotch/hoppscotch:latest
  ```

---

## 통합 아키텍처 예시

```text
┌─────────────────────────────────────┐
│        Client (Web/Mobile)          │
└────────────────┬────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────┐
│      API Gateway (Kong/APISIX)      │
│  • Rate Limiting (Redis)            │
│  • Authentication (OAuth2/JWT)      │
│  • Routing                          │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    Service Discovery (Consul)       │
│  • Health Check                     │
│  • Load Balancing (Nginx)           │
└────────────────┬────────────────────┘
                 │
  ┌──────────────┼──────────────┐
  │              │              │
  ▼              ▼              ▼
Service1     Service2      Service3
(REST)      (gRPC)       (GraphQL)
```

---

## 설치 및 테스트 스크립트

```bash
#!/bin/bash
# 전체 스택 설치

# 1. API Gateway (Kong)
docker-compose -f kong-compose.yml up -d

# 2. Service Discovery (Consul)
docker run -d --name consul \
  -p 8500:8500 consul:latest agent -server -ui -bootstrap-expect=1

# 3. Rate Limiting (Redis)
docker run -d --name redis -p 6379:6379 redis:latest

# 4. 테스트
curl -X POST http://localhost:8001/services/ \
  -d "name=test-service" \
  -d "url=http://localhost:3000"

echo "API Gateway Stack Ready"
```

---

## 참조

- Kong: https://konghq.com/
- APISIX: https://apisix.apache.org/
- Traefik: https://traefik.io/
- Consul: https://www.consul.io/
- OpenAPI: https://spec.openapis.org/
- gRPC: https://grpc.io/
- GraphQL: https://graphql.org/
