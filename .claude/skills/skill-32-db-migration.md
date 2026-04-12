# Skill 32: DB Migration

## 목적
DB 스키마 변경을 안전하게 관리한다. 직접 SQL 수정 금지 규칙 보강.
마이그레이션 파일로 버전 관리.

## 트리거
- "마이그레이션", "db migration", "스키마 변경", "테이블 추가"
- DB 관련 변경 요청 시 자동 활성화

## 실행 흐름

### 1. 마이그레이션 파일 생성
```
migrations/
  V001_create_users.sql
  V002_add_email_column.sql
  V003_create_orders.sql
```

### 2. 프레임워크별 연동
```
Spring Boot: Flyway (V{번호}__{설명}.sql)
Django:      python manage.py makemigrations
SQLAlchemy:  alembic revision --autogenerate
Node.js:     knex migrate:make {name}
```

### 3. 안전 규칙
```
[자동 생성 가능]
  - CREATE TABLE
  - ALTER TABLE ADD COLUMN
  - CREATE INDEX

[수동 확인 필수 — DBA 리뷰]
  - ALTER TABLE DROP COLUMN
  - DROP TABLE
  - 데이터 마이그레이션 (UPDATE/INSERT)
  - 인덱스 변경 (대용량 테이블)

[절대 금지]
  - 프로덕션 DB 직접 수정
  - 롤백 불가능한 DDL
```

### 4. 롤백 스크립트 자동 생성
```
각 마이그레이션에 대응하는 rollback:
  V002_add_email_column.sql      → R002_remove_email_column.sql
  V003_create_orders.sql         → R003_drop_orders.sql
```

## 출력
- `migrations/V{N}_{name}.sql`
- `migrations/R{N}_{name}.sql` (롤백)
- `docs/YYYY-MM-DD/migration-plan.md`
