# virtualization-mcp API Documentation

## Introduction

The virtualization-mcp API provides a comprehensive interface for managing virtual machines, containers, and related resources. The API follows RESTful principles and uses JSON for request and response bodies.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000/api/v1
```

## Authentication

virtualization-mcp supports the following authentication methods:

1. **API Key**
   - Include in the `X-API-Key` header
   - Example: `X-API-Key: your-api-key-here`

2. **OAuth2**
   - Use the `/auth/token` endpoint to obtain a token
   - Include the token in the `Authorization` header
   - Example: `Authorization: Bearer your-token-here`

## Response Format

All API responses follow a standard format:

```json
{
  "status": "success",
  "data": {},
  "meta": {},
  "error": null
}
```

### Response Fields

| Field    | Type   | Description                                      |
|----------|--------|--------------------------------------------------|
| status   | string | `success` or `error`                             |
| data     | object | The response data (null if error)               |
| meta     | object | Additional metadata (pagination, timestamps, etc) |
| error    | object | Error details (null if successful)               |

## Error Handling

Errors follow this format:

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {
      "resource": "virtual_machine",
      "id": "12345"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code                | Description                                 |
|-------------|---------------------------|---------------------------------------------|
| 400         | INVALID_REQUEST           | Invalid request parameters                 |
| 401         | UNAUTHORIZED             | Authentication required                    |
| 403         | FORBIDDEN                | Insufficient permissions                   |
| 404         | NOT_FOUND                | Resource not found                         |
| 409         | CONFLICT                 | Resource conflict                          |
| 429         | RATE_LIMIT_EXCEEDED      | Too many requests                          |
| 500         | INTERNAL_SERVER_ERROR    | Server error                               |

## Rate Limiting

API requests are subject to rate limiting:

- 1000 requests per hour per API key
- 100 requests per minute per IP address

Exceeded limits will return a 429 status code with a `Retry-After` header.

## Versioning

The API is versioned through the URL path:

```
/api/v1/...
```

## Date and Time

All dates and times are in UTC and formatted according to ISO 8601:

```
2025-08-01T22:42:33Z
```

## Pagination

Endpoints that return lists of items support pagination:

### Query Parameters

| Parameter | Type    | Default | Description                          |
|-----------|---------|---------|--------------------------------------|
| page      | integer | 1       | Page number (1-based)               |
| per_page  | integer | 20      | Number of items per page (max 100)   |
| sort      | string  | -created| Sort order (prefix with - for desc)  |

### Response Headers

| Header           | Description                          |
|------------------|--------------------------------------|
| X-Total-Count    | Total number of items               |
| X-Page           | Current page number                 |
| X-Per-Page       | Number of items per page            |
| X-Total-Pages    | Total number of pages               |
| Link             | Pagination links (first, prev, next, last) |

## Field Selection

Use the `fields` parameter to request specific fields:

```
GET /api/v1/vms?fields=id,name,status
```

## Related Resources

- [API Reference](/api/reference)
- [Authentication Guide](/docs/authentication)
- [Rate Limiting](/docs/rate-limiting)



