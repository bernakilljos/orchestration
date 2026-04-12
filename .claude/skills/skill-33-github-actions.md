# Skill 33: GitHub Actions (CI/CD)

## 목적
GitHub Actions 워크플로우를 자동 생성한다.
push → 빌드 → 테스트 → 배포 파이프라인.

## 트리거
- "CI/CD", "github actions", "파이프라인", "자동 배포"
- 새 프로젝트 초기 설정 시

## 실행 흐름

### 1. 스택 감지 → 워크플로우 생성
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4  # 또는 python/java
      - run: npm ci
      - run: npm test
      - run: npm run build
```

### 2. 프리셋
```
Node.js:   install → lint → test → build
Python:    install → pytest → mypy
Spring:    mvn test → mvn package
Vue/React: install → lint → test → build → deploy
```

### 3. 배포 워크플로우
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          script: |
            cd /app && git pull && npm ci && pm2 restart all
```

### 4. 보안 체크 워크플로우
```yaml
# .github/workflows/security.yml
- run: npm audit --audit-level=high
- uses: github/codeql-action/analyze@v3
```

## 출력
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/security.yml` (선택)
