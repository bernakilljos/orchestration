# Database & Cache Toolkit — DB·캐시·검색·메시지큐 아키텍처 패턴

> **목적**: Airbnb급 서비스 구축에 필요한 DB/캐시/검색 인프라 패턴 총정리

---

## 1. RDBMS (관계형 DB)

| DB | 특장 | Docker | 클라우드 |
|----|------|--------|----------|
| **PostgreSQL** | 가장 강력한 오픈소스 (JSON, GIS, FTS) | `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pw postgres:16` | AWS RDS, Supabase, Neon |
| **MySQL** | 가장 널리 쓰임 | `docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=pw mysql:8` | AWS RDS, PlanetScale |
| **SQLite** | 파일 기반 (서버 불필요) | 내장 | Turso (분산 SQLite) |
| **MariaDB** | MySQL 포크 (호환) | `docker run -d -p 3306:3306 -e MARIADB_ROOT_PASSWORD=pw mariadb:11` | SkySQL |

### Python ORM
```bash
pip install sqlalchemy         # 표준 ORM
pip install sqlmodel           # SQLAlchemy + Pydantic (FastAPI 최적)
pip install tortoise-orm       # async ORM
pip install peewee             # 경량 ORM
pip install alembic            # DB 마이그레이션
pip install asyncpg            # PostgreSQL async (최고 성능)
pip install aiomysql           # MySQL async
```

### 패턴: FastAPI + SQLModel
```python
from sqlmodel import SQLModel, Field, create_engine, Session
from fastapi import FastAPI

class Listing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    price: float
    city: str

engine = create_engine("postgresql+asyncpg://user:pw@localhost/db")
app = FastAPI()

@app.post("/listings")
def create(listing: Listing):
    with Session(engine) as s:
        s.add(listing); s.commit(); s.refresh(listing)
    return listing
```

---

## 2. NoSQL

### Document DB
| DB | 특장 | Docker |
|----|------|--------|
| **MongoDB** | JSON 문서 (스키마 유연) | `docker run -d -p 27017:27017 mongo:7` |
| **CouchDB** | HTTP API, 자동 복제 | `docker run -d -p 5984:5984 couchdb:3` |
| **Firestore** | Google 서버리스 | Firebase 콘솔 |

```bash
pip install pymongo           # MongoDB
pip install motor             # MongoDB async
pip install firebase-admin    # Firestore
```

### Key-Value / Cache
| DB | 특장 | Docker |
|----|------|--------|
| **Redis** | 캐시 + 메시지 브로커 + 세션 | `docker run -d -p 6379:6379 redis:7` |
| **Valkey** | Redis 오픈소스 포크 | `docker run -d -p 6379:6379 valkey/valkey:7` |
| **Memcached** | 순수 캐시 (심플) | `docker run -d -p 11211:11211 memcached:1.6` |
| **DragonflyDB** | Redis 호환 (25x 빠름) | `docker run -d -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly` |

```bash
pip install redis             # Redis
pip install aioredis          # Redis async
```

### Wide-Column
| DB | 특장 | 용도 |
|----|------|------|
| **Cassandra** | 대규모 쓰기 (IoT, 로그) | `docker run -d -p 9042:9042 cassandra:4` |
| **ScyllaDB** | Cassandra 호환 (10x 빠름) | Docker |
| **HBase** | Hadoop 위 (빅데이터) | Hadoop 클러스터 |

### Graph DB
| DB | 특장 | Docker |
|----|------|--------|
| **Neo4j** | 그래프 DB 표준 (소셜, 추천) | `docker run -d -p 7474:7474 -p 7687:7687 neo4j:5` |
| **ArangoDB** | 멀티모델 (문서+그래프+KV) | Docker |

```bash
pip install neo4j             # Neo4j
pip install pyarango          # ArangoDB
```

### Time-Series
| DB | 특장 | Docker |
|----|------|--------|
| **InfluxDB** | 시계열 표준 (모니터링, IoT) | `docker run -d -p 8086:8086 influxdb:2` |
| **TimescaleDB** | PostgreSQL 확장 (시계열) | `docker run -d -p 5432:5432 timescale/timescaledb:latest-pg16` |
| **QuestDB** | 초고속 시계열 (SQL 호환) | Docker |

---

## 3. 검색 엔진 (Full-Text Search)

| 엔진 | 특장 | Docker |
|------|------|--------|
| **Elasticsearch** | 검색 표준 (FTS + 분석 + 한글) | `docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.13.0` |
| **OpenSearch** | Elasticsearch 오픈소스 포크 (AWS) | Docker |
| **Meilisearch** | 초간단 검색 (typo 허용, 빠름) | `docker run -d -p 7700:7700 getmeili/meilisearch:v1.8` |
| **Typesense** | Meilisearch 대안 (타입 안전) | Docker |
| **Zinc** | 경량 Elasticsearch 대안 (Go) | Docker |

```bash
pip install elasticsearch     # Elasticsearch
pip install opensearch-py     # OpenSearch
pip install meilisearch       # Meilisearch
```

### 한글 검색 (nori 분석기)
```json
// Elasticsearch 한글 인덱스
{
  "settings": {
    "analysis": {
      "analyzer": {
        "korean": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": ["nori_readingform", "lowercase"]
        }
      }
    }
  }
}
```

---

## 4. 벡터 DB (AI 임베딩 검색)

| DB | 특장 | 설치 |
|----|------|------|
| **ChromaDB** | 로컬 벡터 DB (이미 설치 가능) | `pip install chromadb` |
| **Pinecone** | 클라우드 벡터 DB (관리형) | `pip install pinecone-client` |
| **Weaviate** | 벡터 + 키워드 하이브리드 | Docker |
| **Qdrant** | Rust 기반 고속 벡터 | Docker |
| **Milvus** | 대규모 벡터 (1B+) | Docker |
| **pgvector** | PostgreSQL 벡터 확장 | SQL extension |
| **LanceDB** | 서버리스 벡터 (파일 기반) | `pip install lancedb` |

```python
# ChromaDB — RAG 용
import chromadb
client = chromadb.Client()
collection = client.create_collection("docs")
collection.add(documents=["텍스트"], ids=["1"])
results = collection.query(query_texts=["검색어"], n_results=5)
```

---

## 5. 메시지 큐 / 이벤트 스트리밍

| 시스템 | 특장 | Docker |
|--------|------|--------|
| **Redis Pub/Sub** | 간단한 실시간 메시징 | Redis 내장 |
| **RabbitMQ** | AMQP 표준 (라우팅 강력) | `docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management` |
| **Apache Kafka** | 대규모 이벤트 스트리밍 | Docker Compose |
| **NATS** | 초경량 메시징 (클라우드 네이티브) | `docker run -d -p 4222:4222 nats:2` |
| **AWS SQS** | 관리형 큐 | boto3 |
| **BullMQ** | Node.js Redis 기반 큐 | `npm install bullmq` |
| **Celery** | Python 분산 태스크 큐 | `pip install celery[redis]` |

```python
# Celery + Redis — 비동기 태스크
from celery import Celery
app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def process_video(path):
    # 영상 복원 작업 (백그라운드)
    return upscale(path)

# 호출
process_video.delay('old_video.mp4')
```

---

## 6. 캐시 패턴

### Cache-Aside (Lazy Loading)
```python
def get_listing(id):
    cached = redis.get(f"listing:{id}")
    if cached: return json.loads(cached)
    listing = db.query(Listing).get(id)
    redis.setex(f"listing:{id}", 3600, json.dumps(listing))
    return listing
```

### Write-Through
```python
def update_listing(id, data):
    db.query(Listing).filter_by(id=id).update(data)
    redis.setex(f"listing:{id}", 3600, json.dumps(data))
```

### Write-Behind (Async)
```python
def update_listing(id, data):
    redis.setex(f"listing:{id}", 3600, json.dumps(data))
    queue.enqueue('sync_to_db', id, data)  # 비동기 DB 반영
```

### Cache Invalidation
```python
def delete_listing(id):
    db.query(Listing).filter_by(id=id).delete()
    redis.delete(f"listing:{id}")
    redis.delete("listings:all")  # 관련 캐시도 삭제
```

---

## 7. DB 스케일링 패턴

### Read Replica (읽기 분산)
```text
Writer (Primary) → Reader 1 (Replica)
                 → Reader 2 (Replica)
                 → Reader 3 (Replica)
```

### Sharding (수평 분할)
```text
User ID % 4 = 0 → Shard 0 (서울)
User ID % 4 = 1 → Shard 1 (도쿄)
User ID % 4 = 2 → Shard 2 (싱가포르)
User ID % 4 = 3 → Shard 3 (미국)
```

### CQRS (Command Query Responsibility Segregation)
```text
Write → PostgreSQL (정합성)
Read  → Elasticsearch (검색) + Redis (캐시)
Sync  → Kafka/Debezium (CDC)
```

---

## 8. docker-compose 통합 예시

```yaml
# Airbnb급 로컬 개발 스택
version: '3.8'
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: app
    volumes: ["pg_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  elasticsearch:
    image: elasticsearch:8.13.0
    ports: ["9200:9200"]
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"

  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]

  meilisearch:
    image: getmeili/meilisearch:v1.8
    ports: ["7700:7700"]

  grafana:
    image: grafana/grafana:10
    ports: ["3000:3000"]

  prometheus:
    image: prom/prometheus:v2
    ports: ["9090:9090"]

volumes:
  pg_data:
```

---

## 추천 조합

### MVP (최소)
```text
SQLite + Redis + Meilisearch
```

### 중규모 서비스
```text
PostgreSQL + Redis + Elasticsearch + RabbitMQ + Celery
```

### 대규모 (Airbnb급)
```text
PostgreSQL (Sharded) + Redis Cluster + Elasticsearch + Kafka + Cassandra (로그)
```

### AI 서비스
```text
PostgreSQL + ChromaDB/pgvector + Redis + Celery
```
