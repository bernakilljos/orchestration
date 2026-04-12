# API Specification — [Domain Name]

## Basic Info

- Base URL: `process.env.VUE_APP_API_URL`
- Content-Type: `application/json`
- Auth: Bearer Token (Authorization header)

---

## [API Name]

### GET /api/v1/[resource]

**Description**: [What this API does]

**Request**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | Integer | N | Page number (default: 0) |
| size | Integer | N | Page size (default: 20) |
| [param] | [type] | Y/N | [Description] |

**Response 200**

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

**Response 400**

```json
{
  "code": "400",
  "message": "[Error message]",
  "data": null
}
```

---

### POST /api/v1/[resource]

**Description**: [What this API does]

**Request Body**

```json
{
  "[field]": "[value]",
  "[field2]": "[value2]"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| [field] | String | Y | [Description] |
| [field2] | Integer | N | [Description] |

**Response 200**

```json
{
  "code": "200",
  "message": "SUCCESS",
  "data": {
    "id": "[Created ID]"
  }
}
```

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Request parameter error |
| 401 | Unauthorized | Authentication failed |
| 403 | Forbidden | No permission |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

## Vue Call Example

```javascript
// Use process.env (hardcoding prohibited)
const response = await this.$http.get(
  `${process.env.VUE_APP_API_URL}/api/v1/[resource]`,
  { params: { page: 0, size: 20 } }
)
```
