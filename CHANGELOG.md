# Changelog

All notable changes to ThreatScan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Added public deployment guidance for Vercel + backend stack to prevent frontend `Failed to fetch` caused by localhost API URLs.
- Updated `.env.example` defaults for production sharing (`NEXT_PUBLIC_API_URL` placeholder and Vercel origin in `CORS_ORIGINS`).
- Added `render.yaml` blueprint for deploying API, worker, beat, PostgreSQL, Redis, and MinIO on Render.
- Added `frontend/vercel.json` and an exact Vercel settings checklist (root directory, env scopes, redeploy validation).
- Fixed Render blueprint schema by removing invalid `startCommand` from Docker-runtime services and adding `backend/Dockerfile.beat` for the beat worker.

## [0.1.0] - 2026-03-01

### Added
- Initial release of ThreatScan
- File upload with SHA256/SHA1/MD5 hashing and deduplication
- 8-stage static analysis pipeline (Celery workers)
  - File metadata extraction
  - Shannon entropy calculation
  - ASCII/Unicode string extraction (up to 5,000 strings)
  - IOC extraction (IPs, domains, URLs, emails)
  - YARA rule scanning with severity scoring
  - PE header/section/import analysis
  - Automated threat scoring (0-100) with verdict classification
  - Comprehensive report generation
- 12 built-in YARA rules across 2 rule files
  - `malware_core.yar`: PE packers, macros, PowerShell, process injection, ransomware, keyloggers
  - `suspicious_indicators.yar`: Base64 blobs, obfuscation, network IOCs, anti-analysis, persistence, crypto mining
- Next.js 14 frontend with dark theme
  - File upload with drag-and-drop
  - Real-time job status polling
  - Multi-tab report viewer (Overview, Details, Strings, IOCs, Relations, Community)
  - Search by hash, IP, domain, or URL
  - Indicator pivot pages
  - Admin dashboard with job management
- FastAPI REST API with 10+ endpoints
- PostgreSQL database with UUID primary keys, JSONB, trigram search
- MinIO S3-compatible file storage
- Docker Compose deployment (7 services)
- Rate limiting (30 req/min per IP)
- File size (50 MB) and MIME type validation
- Community features: comments and tags on reports
- Alembic database migration support
- GitHub Actions CI/CD pipeline
- Comprehensive test suite (pytest)

### Security
- Non-root container execution
- `no-new-privileges` security option
- Magic-byte MIME verification
- SQL injection protection via SQLAlchemy parameterized queries
- CORS origin restriction
- Network isolation via Docker bridge network
