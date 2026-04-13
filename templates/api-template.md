# API 명세 — [도메인명]

## 기본 정보

- Base URL: `[환경변수 참조 — 예: process.env.API_URL]`
- Content-Type: `application/json`
- 인증: Bearer Token (Authorization 헤더)

---

## [API명]

### GET /api/v1/[리소스]

**설명**: [이 API가 하는 일]

**요청 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | Integer | N | 페이지 번호 (기본: 0) |
| size | Integer | N | 페이지 크기 (기본: 20) |
| [파라미터] | [타입] | Y/N | [설명] |

**응답 200**

```json
{
  "code": "200",
  "message": "SUCCESS",
  "data": {
    "content": [],
    "totalElements": 0,
    "totalPages": 0,
    "number": 0,
    "size": 20
  }
}
```

**응답 400**

```json
{
  "code": "400",
  "message": "[에러 메시지]",
  "data": null
}
```

---

### POST /api/v1/[리소스]

**설명**: [이 API가 하는 일]

**요청 바디**

```json
{
  "[필드]": "[값]",
  "[필드2]": "[값2]"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| [필드] | String | Y | [설명] |
| [필드2] | Integer | N | [설명] |

**응답 200**

```json
{
  "code": "200",
  "message": "SUCCESS",
  "data": {
    "id": "[생성된 ID]"
  }
}
```

---

## 에러 코드

| 코드 | 메시지 | 설명 |
|------|--------|------|
| 400 | Bad Request | 요청 파라미터 오류 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 500 | Internal Server Error | 서버 오류 |

## 호출 예시

```javascript
// 환경변수 사용 (하드코딩 금지)
const response = await fetch(
  `${API_BASE_URL}/api/v1/[리소스]`,
  { method: 'GET', headers: { 'Authorization': `Bearer ${token}` } }
)
```
