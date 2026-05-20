# Message Queue & Event-Driven (Advanced) Toolkit

> **목적**: 메시지 큐·이벤트 스트리밍 관련 80+ 공통 도구 레퍼런스
> **적용**: Kafka·RabbitMQ·Saga 패턴·CQRS·Event Sourcing 등
> **최신**: 2026-05-20

---

## 1. 메시지 브로커 (Message Broker)

### Apache Kafka
- **용도**: 고처리량 이벤트 스트리밍, 로그 집계
- **특징**: 분산, 확장성, 순서 보장 (파티션 내)
- **설치**:
  ```bash
  # Docker
  docker-compose -f kafka-compose.yml up -d
  
  # 직접 설치 (macOS)
  brew install kafka
  zookeeper-server-start /usr/local/etc/kafka/zookeeper.properties &
  kafka-server-start /usr/local/etc/kafka/server.properties &
  ```
- **주제 생성**:
  ```bash
  kafka-topics --create --topic my-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
  ```
- **프로듀서** (Python):
  ```bash
  pip install kafka-python
  ```
  ```python
  from kafka import KafkaProducer
  import json
  
  producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
  )
  
  producer.send('my-topic', {'message': 'Hello, Kafka!'})
  producer.flush()
  ```
- **컨슈머**:
  ```python
  from kafka import KafkaConsumer
  
  consumer = KafkaConsumer(
    'my-topic',
    bootstrap_servers=['localhost:9092'],
    group_id='my-group',
    auto_offset_reset='earliest'
  )
  
  for message in consumer:
    print(message.value)
  ```

### RabbitMQ
- **용도**: 신뢰성 높은 메시지 큐, 작업 큐
- **특징**: AMQP 프로토콜, 메시지 확인(acknowledgment)
- **설치**:
  ```bash
  # Ubuntu
  sudo apt-get install rabbitmq-server
  sudo systemctl start rabbitmq-server
  
  # Docker
  docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
  ```
- **관리 UI**: http://localhost:15672 (기본 guest/guest)
- **프로듀서** (Python):
  ```bash
  pip install pika
  ```
  ```python
  import pika
  import json
  
  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  
  channel.queue_declare(queue='my_queue', durable=True)
  channel.basic_publish(
    exchange='',
    routing_key='my_queue',
    body=json.dumps({'message': 'Hello, RabbitMQ!'})
  )
  connection.close()
  ```
- **컨슈머**:
  ```python
  def callback(ch, method, properties, body):
    print(f"Received: {body}")
    ch.basic_ack(delivery_tag=method.delivery_tag)
  
  channel.basic_consume(queue='my_queue', on_message_callback=callback)
  channel.start_consuming()
  ```

### Redis Streams
- **용도**: Redis 기반 메시지 큐, 이벤트 로그
- **특징**: Redis 의 단순성, 지속성
- **사용** (Python):
  ```python
  import redis
  
  r = redis.Redis()
  
  # 메시지 추가
  message_id = r.xadd('my-stream', {'field': 'value'})
  
  # 읽기
  messages = r.xrange('my-stream')
  
  # 컨슈머 그룹
  r.xgroup_create('my-stream', 'my-group', id='0', mkstream=True)
  pending = r.xreadgroup({'my-group': '>'}, 'consumer1', streams=['my-stream'])
  ```

### NATS
- **용도**: 경량 메시징, 마이크로서비스
- **특징**: Go 기반, 매우 빠름, pub-sub + queue
- **설치**:
  ```bash
  docker run -d -p 4222:4222 nats:latest
  ```
- **클라이언트** (Node.js):
  ```bash
  npm install nats
  ```
  ```javascript
  const { connect } = require('nats');
  
  const nc = await connect({ servers: "localhost:4222" });
  
  // Pub-Sub
  nc.publish('subject', 'Hello NATS!');
  
  const sub = nc.subscribe('subject');
  for await (const m of sub) {
    console.log(m.data);
  }
  ```

### Apache Pulsar
- **용도**: 멀티테넌트, 지연 시간 낮은 메시징
- **특징**: Kafka + RabbitMQ 장점 결합
- **설치**:
  ```bash
  docker run -d -p 6650:6650 -p 8080:8080 apachepulsar/pulsar:latest
  ```

### Redpanda
- **용도**: Kafka 호환, 더 빠름
- **특징**: C++ 기반, 낮은 지연 시간
- **설치**:
  ```bash
  docker run -d --name redpanda -p 9092:9092 redpandadata/redpanda:latest
  ```

---

## 2. 이벤트 스트리밍 (Event Streaming)

### Kafka Streams
- **용도**: Kafka 토픽에서 스트림 처리
- **예시** (Java):
  ```java
  StreamsBuilder builder = new StreamsBuilder();
  
  builder.stream("input-topic")
    .filter((key, value) -> value.length() > 5)
    .to("output-topic");
  
  KafkaStreams streams = new KafkaStreams(builder.build(), props);
  streams.start();
  ```

### Apache Flink
- **용도**: 대규모 스트림 처리, 복잡한 이벤트 처리
- **특징**: 높은 처리량, 정확한 전달 보장
- **설치**:
  ```bash
  docker run -d --name flink-jobmanager \
    -p 8081:8081 \
    flink:latest jobmanager
  ```

### Apache Spark Streaming
- **용도**: 마이크로배치 스트림 처리
- **특징**: Spark 생태계 통합
- **예시** (PySpark):
  ```python
  from pyspark.sql import SparkSession
  
  spark = SparkSession.builder.appName("streaming").getOrCreate()
  df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "my-topic") \
    .load()
  
  df.writeStream.format("console").start().awaitTermination()
  ```

### Benthos
- **용도**: 경량 스트림 처리, 데이터 파이프라인
- **설치**:
  ```bash
  docker run -d -p 4195:4195 jeffail/benthos:latest
  ```

---

## 3. 이벤트 소싱 (Event Sourcing)

### EventStoreDB
- **용도**: 이벤트 스토어 (전용 DB)
- **설치**:
  ```bash
  docker run -d \
    -p 2113:2113 \
    -p 1113:1113 \
    eventstore/eventstore:latest
  ```
- **이벤트 저장** (Python):
  ```python
  import httpx
  
  client = httpx.Client(base_url="http://localhost:2113")
  
  event = {
    "eventType": "UserCreated",
    "data": {"userId": "123", "email": "user@example.com"}
  }
  
  response = client.post(
    "/streams/users",
    json=[event],
    headers={"Content-Type": "application/json"}
  )
  ```

### Axon Framework (Java)
- **용도**: CQRS + Event Sourcing 프레임워크
- **의존성** (Maven):
  ```xml
  <dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-spring-boot-starter</artifactId>
    <version>4.7.0</version>
  </dependency>
  ```
- **이벤트 정의**:
  ```java
  @Value
  @EqualsAndHashCode(callSuper = false)
  public class UserCreatedEvent extends AbstractDomainEvent {
    String userId;
    String email;
  }
  ```

### Marten (.NET)
- **용도**: PostgreSQL 기반 Event Sourcing
- **설치** (NuGet):
  ```text
  Install-Package Marten
  ```

---

## 4. CQRS (Command Query Responsibility Segregation)

### MediatR (C#/.NET)
- **설치** (NuGet):
  ```text
  Install-Package MediatR
  ```

- **커맨드**:
  ```csharp
  public class CreateUserCommand : IRequest<Guid> {
    public string Email { get; set; }
  }
  
  public class CreateUserCommandHandler : IRequestHandler<CreateUserCommand, Guid> {
    public async Task<Guid> Handle(CreateUserCommand request, CancellationToken ct) {
      var userId = Guid.NewGuid();
      // 처리 로직
      return userId;
    }
  }
  ```

### Brighter (C#/.NET)
- **설치** (NuGet):
  ```text
  Install-Package Paramore.Brighter
  ```

### EventFlow (C#/.NET)
- **특징**: CQRS, Event Sourcing 통합

### Wolverine (C#/.NET 최신)
- **설치** (NuGet):
  ```text
  Install-Package Wolverine
  ```

---

## 5. Saga 패턴 (Saga Pattern)

### Temporal (분산 워크플로우)
- **용도**: 분산 트랜잭션, 장시간 실행 프로세스
- **설치**:
  ```bash
  git clone https://github.com/temporalio/temporal
  cd temporal && docker-compose up
  ```
- **워크플로우** (Python):
  ```bash
  pip install temporalio
  ```
  ```python
  from temporalio import workflow
  
  @workflow.defn
  class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str):
      await workflow.execute_activity(
        charge_payment,
        args=[order_id],
        start_to_close_timeout=timedelta(minutes=5)
      )
      await workflow.execute_activity(
        reserve_inventory,
        args=[order_id]
      )
  ```

### Cadence (Uber)
- **용도**: Temporal 이전 버전, 여전히 사용 중
- **특징**: 실패 처리, 재시도 자동

### MassTransit (C#/.NET)
- **설치** (NuGet):
  ```text
  Install-Package MassTransit
  ```

- **Saga**:
  ```csharp
  public class OrderSaga : ISaga {
    public Guid CorrelationId { get; set; }
  }
  ```

### NServiceBus (C#/.NET)
- **용도**: 엔터프라이즈 메시징, Saga 지원
- **특징**: 높은 신뢰성

---

## 6. 스키마 레지스트리 (Schema Registry)

### Confluent Schema Registry
- **용도**: Kafka 메시지 스키마 관리 (Avro, Protobuf, JSON Schema)
- **설치**:
  ```bash
  docker run -d \
    -p 8081:8081 \
    -e SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS="kafka:9092" \
    confluentinc/cp-schema-registry:7.5.0
  ```
- **스키마 등록** (REST API):
  ```bash
  curl -X POST http://localhost:8081/subjects/users-value/versions \
    -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    -d '{
      "schema": "{\"type\":\"record\",\"name\":\"User\",\"fields\":[{\"name\":\"id\",\"type\":\"int\"},{\"name\":\"email\",\"type\":\"string\"}]}"
    }'
  ```

### Karapace (Aiven)
- **용도**: 오픈소스 Schema Registry
- **설치**:
  ```bash
  pip install karapace
  karapace rest --config config.yml
  ```

### Apicurio
- **용도**: 오픈소스 스키마 레지스트리 + API 설계
- **설치**:
  ```bash
  docker run -d -p 8080:8080 apicurio/apicurio-registry:latest
  ```

---

## 7. 모니터링 (Monitoring)

### Kafka UI
- **용도**: Kafka 웹 관리 UI
- **설치**:
  ```bash
  docker run -d \
    -p 8080:8080 \
    -e KAFKA_CLUSTERS_0_NAME=local \
    -e KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092 \
    provectuslabs/kafka-ui:latest
  ```

### RabbitMQ Management
- **UI**: http://localhost:15672
- **기본 자격증명**: guest / guest

### AKHQ (Kafkahq)
- **용도**: Kafka 탐색 UI
- **설치**:
  ```bash
  docker run -d \
    -p 8080:8080 \
    -e AKHQ_CONFIGURATION_BROKERS_0_NAME=kafka \
    -e AKHQ_CONFIGURATION_BROKERS_0_BOOTSTRAPSERVERS=kafka:9092 \
    tchiotlabs/akhq:latest
  ```

### Conduktor
- **용도**: Kafka 고급 관리 (프리미엄)
- **가격**: 무료 플랜 + 유료

### Redpanda Console
- **용도**: Redpanda용 관리 콘솔
- **설치**:
  ```bash
  docker run -d \
    -p 8080:8080 \
    redpandadata/console:latest
  ```

---

## 8. 클라우드 큐 (Cloud Queues)

### AWS SQS (Simple Queue Service)
- **용도**: AWS 관리형 메시지 큐
- **특징**: 완전 관리, 자동 확장
- **Python SDK**:
  ```bash
  pip install boto3
  ```
  ```python
  import boto3
  
  sqs = boto3.client('sqs')
  response = sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue',
    MessageBody='Hello SQS!'
  )
  ```

### AWS SNS (Simple Notification Service)
- **용도**: 팬-아웃, pub-sub 메시징
- **특징**: 여러 구독자에게 메시지 전달

### Azure Service Bus
- **용도**: Azure 관리형 메시징
- **특징**: 큐, 토픽, 구독 지원
- **SDK** (Python):
  ```bash
  pip install azure-servicebus
  ```

### GCP Pub/Sub
- **용도**: Google Cloud 메시징
- **SDK** (Python):
  ```bash
  pip install google-cloud-pubsub
  ```

### CloudAMQP
- **용도**: 관리형 RabbitMQ (SaaS)
- **가격**: 무료 플랜 부터

---

## 9. 경량 큐 (Lightweight Queues)

### BullMQ (Node.js)
- **설치**:
  ```bash
  npm install bullmq
  ```
- **작업 추가**:
  ```javascript
  const { Queue } = require('bullmq');
  
  const queue = new Queue('my-queue', {
    connection: { host: 'localhost', port: 6379 }
  });
  
  await queue.add('job-name', { data: 'value' });
  ```

### Celery (Python)
- **설치**:
  ```bash
  pip install celery[redis]
  ```
- **작업 정의**:
  ```python
  from celery import Celery
  
  app = Celery('tasks', broker='redis://localhost:6379')
  
  @app.task
  def add(x, y):
    return x + y
  
  add.delay(4, 6)
  ```

### Sidekiq (Ruby)
- **설치**:
  ```bash
  gem install sidekiq
  ```

### Faktory
- **용도**: 언어 무관 작업 큐
- **설치**:
  ```bash
  docker run -d -p 7419:7419 contribsys/faktory:latest
  ```

### Bee-Queue (Node.js)
- **설치**:
  ```bash
  npm install bee-queue
  ```

---

## 10. Dead Letter Queue (DLQ) 패턴

### DLQ 구현 전략
- **Kafka DLQ**:
  ```bash
  # 실패 토픽 생성
  kafka-topics --create --topic my-topic-dlq --bootstrap-server localhost:9092
  
  # 컨슈머에서 처리
  try {
    processMessage(message);
  } catch (Exception e) {
    producer.send("my-topic-dlq", message);
  }
  ```

- **RabbitMQ DLQ**:
  ```python
  channel.exchange_declare(exchange='dlx', exchange_type='direct')
  channel.queue_declare(queue='dlq')
  channel.queue_bind(exchange='dlx', queue='dlq', routing_key='failed')
  
  # 주 큐 설정
  channel.queue_declare(
    queue='main_queue',
    arguments={'x-dead-letter-exchange': 'dlx'}
  )
  ```

### 재처리 전략
1. **즉시 재시도**: 실패 즉시 재처리
2. **지수 백오프**: 10s → 1m → 10m → 1h
3. **DLQ 수동 검토**: 운영팀이 분석 후 수정 후 재처리
4. **메트릭 수집**: 재시도 횟수, 실패 원인 기록

### 모니터링
```python
# 메트릭 수집 (Python)
dlq_count = sqs.get_queue_attributes(
  QueueUrl='dlq-url',
  AttributeNames=['ApproximateNumberOfMessages']
)['Attributes']['ApproximateNumberOfMessages']

if int(dlq_count) > 100:
  send_alert("High DLQ count detected")
```

---

## 통합 아키텍처 예시

```text
┌──────────────────────────────┐
│      Event Source            │
│  (User Actions, API Calls)   │
└────────────┬─────────────────┘
             │
┌────────────▼─────────────────┐
│   Message Broker (Kafka)     │
│   ├─ Events Topic            │
│   └─ DLQ Topic               │
└────────────┬─────────────────┘
             │
   ┌─────────┼─────────┐
   │         │         │
   ▼         ▼         ▼
┌─────┐  ┌──────┐  ┌──────────┐
│ ES  │  │CQRS  │  │Workflow  │
│(SES)│  │(View)│  │(Temporal)│
└─────┘  └──────┘  └──────────┘
   │         │         │
   └─────────┼─────────┘
             │
         ┌───▼────┐
         │Metrics │
         │Monitor │
         └────────┘
```

---

## 설치 및 테스트 스크립트

```bash
#!/bin/bash
# 전체 메시징 스택 설치

# 1. Kafka + Zookeeper (docker-compose)
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
EOF

docker-compose up -d

# 2. Schema Registry
docker run -d \
  -p 8081:8081 \
  -e SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS="kafka:9092" \
  confluentinc/cp-schema-registry:7.5.0

# 3. Kafka UI
docker run -d \
  -p 8080:8080 \
  -e KAFKA_CLUSTERS_0_NAME=local \
  -e KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092 \
  provectuslabs/kafka-ui:latest

# 4. 테스트
kafka-topics --create --topic test --bootstrap-server kafka:9092
echo "메시징 스택 준비 완료"
```

---

## 참조

- Kafka: https://kafka.apache.org/
- RabbitMQ: https://www.rabbitmq.com/
- Temporal: https://temporal.io/
- Axon Framework: https://axoniq.io/
- Confluent Schema Registry: https://docs.confluent.io/platform/current/schema-registry/
- AWS SQS: https://aws.amazon.com/sqs/
