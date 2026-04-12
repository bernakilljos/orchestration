# Skill 34: Code Documentation

## 목적
코드에서 API 문서, 함수 문서를 자동 생성한다. JSDoc/Sphinx/Javadoc.

## 트리거
- "문서 생성", "code docs", "API 문서", "JSDoc", "Sphinx"

## 실행 흐름

### 1. 언어별 문서 생성
```
JavaScript/TypeScript:
  → JSDoc 주석 자동 삽입
  → @param, @returns, @throws, @example

Python:
  → Google/NumPy docstring 자동 삽입
  → Sphinx autodoc 연동
  → mkdocs 설정 생성

Java:
  → Javadoc 주석 자동 삽입
  → @param, @return, @throws

Vue:
  → 컴포넌트 Props/Events/Slots 문서화
```

### 2. API 문서 (OpenAPI/Swagger)
```
소스 코드에서 자동 추출:
  Flask:   → openapi.yaml
  Express: → swagger.json
  Spring:  → springdoc 연동
  FastAPI: → /docs 자동 (내장)
```

### 3. 출력 형식
```
docs/api/              Swagger UI (HTML)
docs/api/openapi.yaml  OpenAPI 스펙
docs/code/             코드 문서 (HTML)
```

## 출력
- `docs/api/openapi.yaml`
- `docs/YYYY-MM-DD/code-docs-report.md`
- 소스 코드에 docstring/JSDoc 삽입
