# Skill 30: Docker Compose

## 목적
프로젝트에 맞는 Dockerfile + docker-compose.yml을 자동 생성한다.
개발/스테이징/프로덕션 환경 통일.

## 트리거
- "docker", "컨테이너", "도커", "docker-compose"
- 배포 설정 시 자동 제안

## 실행 흐름

### 1. 스택 감지 → Dockerfile 생성
```
Python/Flask:
  FROM python:3.11-slim
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["python", "main.py"]

Node.js:
  FROM node:20-alpine
  COPY package*.json .
  RUN npm ci --production
  COPY . .
  CMD ["node", "server.js"]

Spring Boot:
  FROM eclipse-temurin:11-jre
  COPY target/*.jar app.jar
  ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 2. docker-compose.yml 생성
```yaml
services:
  app:
    build: .
    ports: ["8080:8080"]
    env_file: .env
    depends_on: [db]
  db:
    image: mysql:8.0
    volumes: [db_data:/var/lib/mysql]
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
```

### 3. 환경별 분리
```
docker-compose.yml          # 기본 (개발)
docker-compose.prod.yml     # 프로덕션 오버라이드
docker-compose.test.yml     # 테스트용
.dockerignore               # 불필요 파일 제외
```

## 출력
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
