# Contributing to ThreatScan

Thank you for your interest in contributing to ThreatScan! This guide will help
you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you agree to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/threatscan.git
   cd threatscan
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/threatscan.git
   ```

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for backend development)
- Node.js 20+ (for frontend development)
- Make (optional, for convenience commands)

### Quick Start (Docker)

```bash
cp .env.example .env
docker compose up -d
```

### Local Development (without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install ruff mypy pytest pytest-asyncio pytest-cov httpx

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Worker

```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info -Q analysis
```

## Project Structure

```
ThreatScan/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── config.py     # Pydantic settings
│   │   ├── database.py   # SQLAlchemy engine & sessions
│   │   ├── main.py       # FastAPI app entry point
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── routes/       # API route handlers
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (storage, validation)
│   │   └── worker/       # Celery tasks & analysis pipeline
│   └── tests/            # pytest test suite
├── frontend/             # Next.js 14 application
│   └── src/
│       ├── app/          # App Router pages
│       ├── components/   # Reusable React components
│       └── lib/          # API client & utilities
├── database/             # SQL initialization scripts
├── yara-rules/           # YARA rule files
└── docs/                 # Documentation
```

## Making Changes

1. Create a **feature branch** from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```
2. Make your changes in small, focused commits
3. Write or update tests for your changes
4. Ensure all tests pass
5. Push and open a Pull Request

### Branch Naming

- `feature/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation updates
- `refactor/description` — code refactoring

## Coding Standards

### Python (Backend)

- **Formatter:** ruff format (Black-compatible)
- **Linter:** ruff check
- **Type hints:** Required for all function signatures
- **Docstrings:** Google style for public functions
- **Imports:** sorted by ruff (isort-compatible)

```bash
# Check code
ruff check backend/app/
ruff format --check backend/app/

# Auto-fix
ruff check --fix backend/app/
ruff format backend/app/
```

### TypeScript (Frontend)

- **Linter:** ESLint with Next.js config
- **Formatter:** Prettier (via ESLint)
- **Types:** Strict TypeScript — no `any` where avoidable

```bash
cd frontend
npx next lint
npx tsc --noEmit
```

### YARA Rules

- One rule per logical detection
- Include `meta:` section with `description`, `author`, `severity`
- Use tags: `critical`, `high`, `medium`, `low`
- Test rules before submitting

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Adding Tests

- Place tests in `backend/tests/`
- Use `pytest-asyncio` for async tests
- Use `httpx.AsyncClient` for API endpoint tests
- Mock external services (MinIO, Redis) in unit tests

### Test Categories

- **Unit tests:** `tests/test_*.py` — test individual functions
- **Integration tests:** `tests/integration/test_*.py` — test with DB
- **API tests:** `tests/api/test_*.py` — test HTTP endpoints

## Submitting Changes

1. Push your branch to your fork
2. Open a Pull Request against `main`
3. Fill out the PR template completely
4. Wait for CI checks to pass
5. Request review from a maintainer

### PR Guidelines

- Keep PRs focused — one feature/fix per PR
- Update documentation if behavior changes
- Add a changelog entry for user-facing changes
- Squash commits before merging if requested

## Adding YARA Rules

YARA rules are a great way to contribute! To add a new rule:

1. Add the rule to an existing `.yar` file or create a new one in `yara-rules/`
2. Include proper metadata:
   ```yara
   rule My_Detection : high
   {
       meta:
           description = "Detects something specific"
           author = "Your Name"
           severity = "high"
           date = "2026-01-01"
       strings:
           $s1 = "pattern" ascii
       condition:
           $s1
   }
   ```
3. Test locally: `python -c "import yara; yara.compile('yara-rules/your_file.yar')"`
4. Open a PR with your rule and a description of what it detects

## Questions?

Open a [Discussion](https://github.com/OWNER/threatscan/discussions) or an Issue.
We're happy to help!
