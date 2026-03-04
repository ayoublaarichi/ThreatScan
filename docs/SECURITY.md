# ThreatScan — Security Configuration & Hardening Guide

This document describes the security controls built into ThreatScan and
recommended production hardening steps.

---

## 1. Application-Level Security

### 1.1 File Upload Validation
| Control | Implementation |
|---------|---------------|
| Max file size | 50 MB enforced in `validation.py` **before** storage |
| MIME allowlist | Only accepted types: `application/x-dosexec`, `application/x-executable`, `application/x-elf`, `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.*`, `application/zip`, `application/x-rar-compressed`, `application/x-7z-compressed`, `application/gzip`, `application/octet-stream` |
| Magic-byte verification | Uses `python-magic` (libmagic) to verify file content matches declared type |
| SHA-256 deduplication | Identical files are stored once; subsequent uploads increment `upload_count` |

### 1.2 Rate Limiting
- **Engine:** slowapi (built on limits / redis)
- **Default:** 30 requests/minute per client IP
- **Configurable:** `RATE_LIMIT` environment variable
- Applied globally via FastAPI middleware

### 1.3 CORS
- Origins restricted via `CORS_ORIGINS` environment variable
- Default: `http://localhost:3000` (dev only)
- **Production:** Set to your exact frontend domain(s)

### 1.4 Input Validation
- All API inputs validated with Pydantic v2 strict schemas
- Path parameters (SHA256, UUID) validated with regex/type constraints
- Search queries sanitized before database use
- SQL injection mitigated via SQLAlchemy parameterized queries

---

## 2. Infrastructure Security

### 2.1 Container Hardening
```yaml
# All application containers run as non-root
security_opt:
  - no-new-privileges:true
```

| Container | User | UID |
|-----------|------|-----|
| api       | `threatscan` | 1000 |
| worker    | `threatscan` | 1000 |
| web (Next.js) | `nextjs` | 1001 |

### 2.2 Network Isolation
The `docker-compose.yml` creates a dedicated `threatscan` bridge network.
Only the API (`:8000`) and frontend (`:3000`) ports are exposed to the host.

**Production recommendation:**
```yaml
# Add port binding to localhost only
ports:
  - "127.0.0.1:8000:8000"
  - "127.0.0.1:3000:3000"
```

### 2.3 Database Security
- PostgreSQL listens only on the Docker network (not exposed to host)
- Credentials via environment variables (never hardcoded)
- `pg_trgm` extension for search — no raw SQL concatenation
- UUID primary keys prevent enumeration attacks

### 2.4 Object Storage (MinIO)
- Internal network only by default
- Bucket created automatically by init container
- Console port `9001` exposed for admin — **bind to localhost in production**
- Credentials via environment variables

### 2.5 Redis
- No authentication by default (internal network only)
- **Production:** Enable `requirepass` in Redis config

---

## 3. Secrets Management

### 3.1 Environment Variables
All secrets are configured via `.env` file (excluded from git via `.gitignore`).

| Variable | Purpose | Example |
|----------|---------|---------|
| `POSTGRES_PASSWORD` | Database password | `<random 32+ chars>` |
| `MINIO_ROOT_USER` | Storage admin user | `threatscan-admin` |
| `MINIO_ROOT_PASSWORD` | Storage admin password | `<random 32+ chars>` |
| `SECRET_KEY` | App signing key | `<random 64 hex chars>` |

### 3.2 Production Recommendations
```bash
# Generate secure passwords
openssl rand -hex 32   # For POSTGRES_PASSWORD
openssl rand -hex 32   # For MINIO_ROOT_PASSWORD
openssl rand -hex 32   # For SECRET_KEY
```

- Use Docker Secrets or Vault in Kubernetes deployments
- Rotate credentials periodically
- Never commit `.env` files to version control

---

## 4. Static Analysis Safety

ThreatScan performs **static analysis only** — uploaded files are never executed.

| Safety Measure | Description |
|----------------|-------------|
| No execution | Files are only read as byte streams |
| No decompression bombs | File size checked before processing |
| YARA scanning | Pattern matching only, no code evaluation |
| PE parsing | `pefile` library reads headers/metadata only |
| String extraction | Regex-based, bounded to 5000 strings max |
| Temp file cleanup | Worker downloads to temp directory, deleted after analysis |

### 4.1 Worker Isolation
- Workers run in dedicated containers separate from the API
- Each analysis task has a 300-second timeout (`task_time_limit`)
- Soft timeout at 270 seconds for graceful shutdown
- Failed tasks retry up to 3 times with exponential backoff

---

## 5. Logging & Monitoring

### 5.1 Structured Logging
- **Library:** structlog with JSON output in production
- **Fields:** timestamp, level, event, request_id, user_ip
- All analysis stages logged with timing information
- Error traces captured with full context

### 5.2 Health Endpoint
```
GET /api/v1/health → {"status": "ok", "version": "0.1.0"}
```
Use for load balancer health checks and uptime monitoring.

### 5.3 Recommended Monitoring
- **Prometheus:** Export Celery task metrics via `celery-prometheus-exporter`
- **Grafana:** Dashboard for scan throughput, queue depth, error rates
- **Alerting:** Alert on worker queue backlog > 100, error rate > 5%

---

## 6. Production Deployment Checklist

- [ ] Generate strong passwords for all services (see §3.2)
- [ ] Set `DEBUG=false` in environment
- [ ] Set `CORS_ORIGINS` to exact frontend domain
- [ ] Bind exposed ports to `127.0.0.1` only
- [ ] Place a reverse proxy (nginx/Caddy) in front with TLS
- [ ] Enable Redis authentication (`requirepass`)
- [ ] Set up database backups (pg_dump cron or WAL archiving)
- [ ] Configure log aggregation (ELK, Loki, CloudWatch)
- [ ] Set up monitoring and alerting (Prometheus + Grafana)
- [ ] Enable container resource limits (CPU/memory)
- [ ] Run security scanner on containers (Trivy, Grype)
- [ ] Set up Alembic for database migrations (see §7)
- [ ] Review and update YARA rules regularly
- [ ] Test rate limiting under load

---

## 7. Database Migrations (Alembic)

For production deployments, use Alembic instead of `init_db()`:

```bash
cd backend
alembic init alembic
# Configure alembic.ini with your DATABASE_URL
# Then:
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

The provided `database/init.sql` can bootstrap a fresh database directly.

---

## 8. TLS / HTTPS Configuration

### Recommended: Caddy Reverse Proxy
```Caddyfile
threatscan.example.com {
    reverse_proxy /api/* localhost:8000
    reverse_proxy /* localhost:3000
}
```
Caddy automatically provisions and renews Let's Encrypt certificates.

### Alternative: nginx + certbot
```nginx
server {
    listen 443 ssl;
    server_name threatscan.example.com;

    ssl_certificate /etc/letsencrypt/live/threatscan.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/threatscan.example.com/privkey.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
