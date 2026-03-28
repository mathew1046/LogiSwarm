# Security

This document describes the security measures implemented in LogiSwarm.

## HTTP Security Headers

All API responses include the following security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS protection for legacy browsers |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer information |
| `Content-Security-Policy` | `default-src 'self'; ...` | Prevents XSS and injection attacks |

## Frontend Security

The frontend (Nginx) also includes these headers:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

## Input Validation

All user inputs are validated using Pydantic models:

1. **Type Validation**: Automatic type coercion and validation
2. **Required Fields**: Explicit nullability declarations
3. **String Constraints**: Min/max length, regex patterns
4. **Numeric Constraints**: Min/max values
5. **Enum Validation**: Only allowed values accepted

Example:
```python
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["viewer", "operator", "admin"]
```

## SQL Injection Prevention

All database queries use SQLAlchemy ORM:

- **No raw SQL** with user input
- **Parameterized queries** via SQLAlchemy
- **Model validation** before persistence

Example:
```python
# Safe - ORM query
result = await db.execute(
    select(DisruptionEvent)
    .where(DisruptionEvent.region_id == region_id)
    .order_by(DisruptionEvent.detected_at.desc())
)

# Never do this:
# result = await db.execute(text(f"SELECT * FROM events WHERE region = '{region}'"))
```

## JWT Authentication

### Token Configuration

- **Algorithm**: HS256
- **Secret Key**: `JWT_SECRET_KEY` environment variable
- **Expiration**: Configurable via `JWT_EXPIRATION_HOURS` (default: 24 hours)

### Secret Rotation Procedure

To rotate the JWT secret:

1. **Generate new secret**:
   ```bash
   NEW_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
   ```

2. **Update environment**:
   ```bash
   # In .env or deployment environment
   JWT_SECRET_KEY_PREVIOUS=${JWT_SECRET_KEY}
   JWT_SECRET_KEY=${NEW_SECRET}
   ```

3. **Deploy and restart services**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --force-recreate backend
   ```

4. **Monitor for authentication errors**:
   ```bash
   docker logs -f logiswarm-backend 2>&1 | grep -i "invalid.*token"
   ```

5. **Force password reset for sensitive accounts** (optional):
   - Admin accounts should reset passwords after key rotation

### Token Validity

- Access tokens expire after configured hours (default: 24)
- Tokens are stateless - no server-side session storage
- Roles: `viewer`, `operator`, `admin`

## Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only access to dashboards and reports |
| `operator` | Accept recommendations, force assessments, configure agents |
| `admin` | Full access including user management and bulk imports |

## Dependency Auditing

### Python Dependencies

Run `pip-audit` in CI pipeline:

```bash
pip-audit --desc DOS --ignore-vuln IDS_TO_IGNORE
```

### JavaScript Dependencies

Run `npm audit` in CI pipeline:

```bash
npm audit --audit-level=moderate
```

### CI Integration

Security scans run automatically on every push:

1. **Dependency vulnerability scan**: `pip-audit` + `npm audit`
2. **Secret scanning**: TruffleHog or Gitleaks
3. **Static analysis**: Bandit (Python)

## Rate Limiting

API rate limiting is implemented using `slowapi`:

- **Global limit**: 1000 requests/minute per IP
- **LLM endpoints**: 10 requests/minute per IP (expensive operations)
- **Auth endpoints**: 20 requests/minute per IP

## CORS Policy

CORS is configured via `CORS_ALLOW_ORIGINS` environment variable:

```bash
# Development
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5001

# Production
CORS_ALLOW_ORIGINS=https://logiswarm.example.com
```

## Secrets Management

### Required Secrets

| Secret | Environment Variable | Purpose |
|--------|---------------------|---------|
| Database Password | `DATABASE_URL` | PostgreSQL connection |
| JWT Secret | `JWT_SECRET_KEY` | Token signing |
| LLM API Key | `LLM_API_KEY` | Claude API access |
| Redis Password | `REDIS_URL` | Redis connection |

### Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** or secret managers
3. **Rotate secrets** regularly (at least annually)
4. **Limit access** to production secrets

## Reporting Security Issues

If you discover a security vulnerability, please report it to:

- Email: security@logiswarm.example.com
- Do not create a public issue

## Security Checklist

- [x] HTTP security headers on all responses
- [x] Input validation with Pydantic
- [x] SQL injection prevention via ORM
- [x] JWT authentication with configurable secret
- [x] RBAC with least-privilege principle
- [x] Rate limiting on expensive endpoints
- [x] CORS policy configuration
- [x] Dependency vulnerability scanning
- [ ] HTTPS enforcement (configure in production)
- [ ] CSP reporting endpoint (optional)