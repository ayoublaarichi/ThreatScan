# ThreatScan — Architecture

```
                         ┌─────────────────────┐
                         │     Web Browser      │
                         └─────────┬────────────┘
                                   │
                          ┌────────▼────────┐
                          │  Next.js 14     │ :3000
                          │  (Frontend)     │
                          └────────┬────────┘
                                   │  REST API calls
                          ┌────────▼────────┐
                          │  FastAPI        │ :8000
                          │  (Backend API)  │
                          └──┬─────┬─────┬──┘
                             │     │     │
               ┌─────────────┤     │     ├─────────────┐
               │             │     │     │             │
       ┌───────▼──────┐  ┌──▼─────▼──┐  │  ┌──────────▼─────┐
       │  PostgreSQL   │  │   Redis   │  │  │     MinIO      │
       │  (Database)   │  │  (Broker) │  │  │  (File Store)  │
       │  :5432        │  │  :6379    │  │  │  :9000/:9001   │
       └───────────────┘  └─────┬─────┘  │  └────────────────┘
                                │        │
                         ┌──────▼────────▼──┐
                         │  Celery Workers   │
                         │  (Analysis)       │
                         │                   │
                         │  ┌─────────────┐  │
                         │  │ 8-Stage     │  │
                         │  │ Pipeline    │  │
                         │  ├─────────────┤  │
                         │  │ 1. Ingest   │  │
                         │  │ 2. Hash     │  │
                         │  │ 3. Metadata │  │
                         │  │ 4. Strings  │  │
                         │  │ 5. IOCs     │  │
                         │  │ 6. YARA     │  │
                         │  │ 7. Score    │  │
                         │  │ 8. Report   │  │
                         │  └─────────────┘  │
                         └───────────────────┘
```

## Data Flow

1. **Upload**: User uploads file via frontend → API validates (size, MIME) → stores in MinIO → creates DB records → dispatches Celery task
2. **Analysis**: Worker downloads from MinIO → runs 8-stage pipeline → writes results to PostgreSQL
3. **Report**: Frontend polls job status → redirects to report page → API assembles report from DB
4. **Search**: Frontend sends query → API classifies (hash/IP/domain/URL) → searches files & indicators → returns results
5. **Pivot**: Click any indicator → API finds all related files sharing that indicator

## Technology Stack

| Layer        | Technology                       |
|-------------|----------------------------------|
| Frontend    | Next.js 14, React 18, TypeScript, TailwindCSS |
| API         | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async)  |
| Workers     | Celery 5.3, yara-python, pefile, python-magic  |
| Database    | PostgreSQL 16 (UUID, JSONB, trigram search)    |
| Queue       | Redis 7 (broker + result backend)              |
| Storage     | MinIO (S3-compatible)                          |
| Deployment  | Docker Compose (7 services)                    |
