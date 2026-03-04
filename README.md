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
