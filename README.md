# ThreatScan

**Open-source malware analysis and threat intelligence platform**

ThreatScan is a public malware analysis platform focused on safe static analysis and indicator intelligence. Users can upload suspicious files, compute hashes, extract indicators, run YARA rules, and generate comprehensive threat reports.

---

## Features

- **File Upload & Hashing** — SHA256, MD5, SHA1 deduplication
- **Static Analysis** — MIME type, entropy, PE header parsing
- **Strings Extraction** — ASCII/Unicode string extraction with filtering
- **IOC Extraction** — Domains, URLs, IP addresses, email addresses
- **YARA Scanning** — Custom rule matching with severity scoring
- **Threat Scoring** — Automated verdict: clean / suspicious / malicious
- **Indicator Pivoting** — Navigate between related samples and indicators
- **Community Features** — Comments and tags on reports
- **Public Report Pages** — Shareable `/report/<sha256>` URLs

---

## Architecture

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Next.js │────▶│ FastAPI │────▶│  Redis  │
│ Frontend │     │   API   │     │  Queue  │
└─────────┘     └────┬────┘     └────┬────┘
                     │               │
                     ▼               ▼
                ┌─────────┐    ┌──────────┐
                │PostgreSQL│    │  Celery  │
                │    DB    │    │ Workers  │
                └─────────┘    └────┬─────┘
                                    │
                               ┌────▼────┐
                               │  MinIO  │
                               │ Storage │
                               └─────────┘
```

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | Next.js 14, React, TypeScript, TailwindCSS |
| Backend    | FastAPI (Python 3.11+)            |
| Workers    | Celery                            |
| Queue      | Redis                             |
| Database   | PostgreSQL 16                     |
| Storage    | MinIO (S3-compatible)             |
| Analysis   | yara-python, python-magic, pefile, lief |
| Deployment | Docker + Docker Compose           |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/threatscan.git
cd threatscan

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Access the platform
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# MinIO:    http://localhost:9001
```

## Public Deployment (Vercel + Backend)

If your shared Vercel URL shows `Failed to fetch`, the frontend is usually trying to call `http://localhost:8000` instead of a public API.

### 1) Deploy backend stack publicly

Deploy these backend services on a public host (VPS, Render, Railway, Fly, etc.):

- FastAPI API (`/health` must be publicly reachable)
- Celery worker
- Celery beat
- PostgreSQL
- Redis
- MinIO (or any S3-compatible storage)

### 2) Configure backend environment

Set these production environment variables for your backend:

- `ENVIRONMENT=production`
- `DEBUG=false`
- `CORS_ORIGINS=https://threatscan-nine.vercel.app`

If you need local + production access, use a comma-separated value:

`CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://threatscan-nine.vercel.app`

### 3) Configure Vercel frontend environment

In Vercel project settings, set:

- `NEXT_PUBLIC_API_URL=https://your-api-domain`

Do not leave this as localhost for production.

### 4) Redeploy and verify

1. Redeploy backend services
2. Redeploy Vercel frontend
3. Verify API health in browser:
     - `https://your-api-domain/health`
4. Open your Vercel site and confirm requests go to your public API domain (Network tab)

### 5) Optional DNS recommendation

Use a dedicated API subdomain such as `https://api.yourdomain.com` and set `NEXT_PUBLIC_API_URL` to that URL.

### 6) Render blueprint option

This repository now includes `render.yaml` to bootstrap backend deployment on Render.

Steps:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint and point it to your repository root.
3. Review generated services from `render.yaml` (`threatscan-api`, `threatscan-worker`, `threatscan-beat`, `threatscan-db`, `threatscan-redis`, `threatscan-minio`).
4. After first deploy, set strong secrets in Render for:
     - `MINIO_SECRET_KEY` (API/worker/beat)
     - `MINIO_ROOT_PASSWORD` (MinIO service)
     - `SECRET_KEY` (all backend services)
     - `ADMIN_PASSWORD` (all backend services)
5. Redeploy all backend services.
6. Copy your public API URL (from `threatscan-api`) and set in Vercel:
     - `NEXT_PUBLIC_API_URL=https://your-api-domain`
7. Redeploy Vercel and verify:
     - `https://your-api-domain/health`

### 7) Exact Vercel checklist (avoid missed settings)

In Vercel project settings:

1. **General**
     - Framework Preset: `Next.js`
     - Root Directory: `frontend`
     - Build Command: `npm run build`
     - Install Command: `npm install`

2. **Environment Variables**
     - `NEXT_PUBLIC_API_URL=https://your-api-domain`
     - `NEXT_PUBLIC_APP_NAME=ThreatScan`

3. **Environment scopes**
     - Add the same `NEXT_PUBLIC_API_URL` value to:
       - Production
       - Preview
       - Development (optional but recommended)

4. **Redeploy frontend**
     - Trigger a new deployment after setting env vars.

5. **Post-deploy validation**
     - Open your Vercel site, open browser DevTools Network tab, and confirm API calls go to `https://your-api-domain` (not localhost).
     - Confirm API health endpoint is reachable:
       - `https://your-api-domain/health`

## API Endpoints

| Method | Endpoint                        | Description              |
|--------|---------------------------------|--------------------------|
| GET    | `/health`                       | Health check             |
| POST   | `/upload`                       | Upload a file            |
| GET    | `/search?q=<query>`             | Search by hash/IOC       |
| GET    | `/report/{sha256}`              | Get scan report          |
| GET    | `/report/{sha256}/relations`    | Get related indicators   |
| GET    | `/indicator/{type}/{value}`     | Pivot on indicator       |
| GET    | `/jobs/{job_id}`                | Check job status         |
| POST   | `/report/{sha256}/comment`      | Add comment              |
| POST   | `/report/{sha256}/tag`          | Add tag                  |
| GET    | `/admin/jobs`                   | Admin: list jobs         |
| POST   | `/admin/delete/{sha256}`        | Admin: delete sample     |

## Scoring System

| Rule                        | Points |
|-----------------------------|--------|
| YARA malware rule hit       | +30    |
| Malicious IOC reputation    | +20    |
| Suspicious macro presence   | +15    |
| Suspicious PowerShell strings | +10  |
| High entropy (>7.0)         | +10    |

| Score Range | Verdict     |
|-------------|-------------|
| 0–24        | Clean       |
| 25–59       | Suspicious  |
| 60–100      | Malicious   |

## Development

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev

# Run workers
cd backend
celery -A app.worker.celery_app worker --loglevel=info
```

## License

MIT License — see [LICENSE](LICENSE) for details.
