# ThreatScan — API Reference
## Base URL
```
http://localhost:8000/api/v1
```

---

## Health Check

### `GET /health`
```bash
curl http://localhost:8000/api/v1/health
```
**Response `200`**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## File Upload

### `POST /upload`
Upload a file for static analysis. Max 50 MB. Accepts binary or PE files.

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@suspicious_sample.exe"
```

**Response `202` — New file**
```json
{
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "queued",
  "message": "File accepted for analysis"
}
```

**Response `200` — Duplicate file (already scanned)**
```json
{
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "job_id": null,
  "status": "already_scanned",
  "message": "File has already been analysed"
}
```

**Response `400` — Validation error**
```json
{
  "detail": "File exceeds maximum allowed size of 52428800 bytes"
}
```

**Response `415` — Unsupported MIME type**
```json
{
  "detail": "MIME type image/png is not accepted for analysis"
}
```

---

## Job Status

### `GET /jobs/{job_id}`
Poll the scan job status. Use 2-second polling interval.

```bash
curl http://localhost:8000/api/v1/jobs/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

**Response `200` — In progress**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "running",
  "stage": "yara_scan",
  "progress": 60,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-03-01T10:30:00Z",
  "updated_at": "2026-03-01T10:30:05Z"
}
```

**Response `200` — Completed**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "stage": "done",
  "progress": 100,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-03-01T10:30:00Z",
  "updated_at": "2026-03-01T10:30:08Z"
}
```

**Response `200` — Failed**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "failed",
  "stage": "error",
  "progress": 0,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-03-01T10:30:00Z",
  "updated_at": "2026-03-01T10:30:03Z"
}
```

**Response `404`**
```json
{
  "detail": "Job not found"
}
```

---

## Report

### `GET /report/{sha256}`
Retrieve the full analysis report for a scanned file.

```bash
curl http://localhost:8000/api/v1/report/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Response `200`** — See [docs/example_report.json](./example_report.json) for a complete example.

**Response `404`**
```json
{
  "detail": "File not found"
}
```

### `GET /report/{sha256}/relations`
Get pivoted file-indicator relationships.

```bash
curl http://localhost:8000/api/v1/report/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/relations
```

**Response `200`**
```json
{
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "indicators": [
    {
      "indicator_type": "domain",
      "value": "malware-c2.example.com",
      "sample_count": 5
    },
    {
      "indicator_type": "ip",
      "value": "185.123.45.67",
      "sample_count": 3
    }
  ],
  "related_files": [
    {
      "sha256": "aabb1122cc...",
      "file_name": "dropper.exe",
      "verdict": "malicious",
      "score": 85,
      "shared_indicator_count": 2
    }
  ]
}
```

---

## Community Features

### `POST /report/{sha256}/comment`
Add a comment to a file report.

```bash
curl -X POST http://localhost:8000/api/v1/report/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/comment \
  -H "Content-Type: application/json" \
  -d '{"content": "Seen in phishing campaign #1234", "author_name": "analyst-one"}'
```

**Response `201`**
```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "content": "Seen in phishing campaign #1234",
  "author_name": "analyst-one",
  "created_at": "2026-03-02T09:15:00Z"
}
```

### `POST /report/{sha256}/tag`
Add a tag to a file report.

```bash
curl -X POST http://localhost:8000/api/v1/report/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/tag \
  -H "Content-Type: application/json" \
  -d '{"name": "trojan", "color": "#ef4444"}'
```

**Response `201`**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "trojan",
  "color": "#ef4444"
}
```

---

## Search

### `GET /search?q={query}`
Search for files by hash (SHA256/SHA1/MD5) or indicators (IP, domain, URL).

```bash
# Search by hash prefix
curl "http://localhost:8000/api/v1/search?q=e3b0c44298fc"

# Search by domain
curl "http://localhost:8000/api/v1/search?q=malware-c2.example.com"

# Search by IP
curl "http://localhost:8000/api/v1/search?q=185.123.45.67"
```

**Response `200`**
```json
{
  "query": "malware-c2.example.com",
  "query_type": "domain",
  "files": [
    {
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "file_name": "suspicious_document.exe",
      "verdict": "malicious",
      "score": 75,
      "first_seen": "2026-03-01T10:30:00Z"
    }
  ],
  "indicators": [
    {
      "indicator_type": "domain",
      "value": "malware-c2.example.com",
      "sample_count": 5,
      "first_seen": "2026-02-15T08:00:00Z"
    }
  ],
  "total": 2
}
```

---

## Indicator Pivot

### `GET /indicator/{type}/{value}`
Get indicator details and all related samples.

```bash
curl "http://localhost:8000/api/v1/indicator/domain/malware-c2.example.com"
```

**Response `200`**
```json
{
  "indicator_type": "domain",
  "value": "malware-c2.example.com",
  "reputation": "malicious",
  "sample_count": 5,
  "first_seen": "2026-02-15T08:00:00Z",
  "last_seen": "2026-03-04T14:22:00Z",
  "files": [
    {
      "sha256": "e3b0c44298fc...",
      "file_name": "suspicious_document.exe",
      "verdict": "malicious",
      "score": 75,
      "first_seen": "2026-03-01T10:30:00Z"
    },
    {
      "sha256": "aabb1122cc...",
      "file_name": "dropper.exe",
      "verdict": "malicious",
      "score": 85,
      "first_seen": "2026-02-20T12:00:00Z"
    }
  ]
}
```

**Response `404`**
```json
{
  "detail": "Indicator not found"
}
```

---

## Admin

### `GET /admin/jobs?status={status}&limit={limit}&offset={offset}`
List scan jobs with optional filtering.

```bash
# All recent jobs
curl "http://localhost:8000/api/v1/admin/jobs?limit=20&offset=0"

# Only failed jobs
curl "http://localhost:8000/api/v1/admin/jobs?status=failed"
```

**Response `200`**
```json
{
  "jobs": [
    {
      "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "completed",
      "stage": "done",
      "progress": 100,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "file_name": "suspicious_document.exe",
      "created_at": "2026-03-01T10:30:00Z",
      "updated_at": "2026-03-01T10:30:08Z"
    }
  ],
  "total": 142,
  "limit": 20,
  "offset": 0
}
```

### `POST /admin/delete/{sha256}`
Delete a file and all associated data (report, indicators, comments, tags, storage).

```bash
curl -X POST "http://localhost:8000/api/v1/admin/delete/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

**Response `200`**
```json
{
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "deleted": true
}
```

---

## Rate Limiting

All endpoints are rate-limited to **30 requests per minute** per IP address.

**Response `429`**
```json
{
  "error": "Rate limit exceeded: 30 per 1 minute"
}
```

---

## Error Responses

All errors follow this structure:
```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning                        |
|-------------|--------------------------------|
| 400         | Bad request / validation error |
| 404         | Resource not found             |
| 413         | File too large                 |
| 415         | Unsupported media type         |
| 429         | Rate limit exceeded            |
| 500         | Internal server error          |
