-- ============================================
-- ThreatScan — Database Initialization Script
-- ============================================
-- This script runs on first container startup
-- via docker-entrypoint-initdb.d/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- trigram index for fuzzy search

-- ── Users ──
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Files ──
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sha256 VARCHAR(64) UNIQUE NOT NULL,
    sha1 VARCHAR(40),
    md5 VARCHAR(32),
    file_name VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(256),
    magic_description TEXT,
    entropy FLOAT,
    storage_path TEXT NOT NULL,
    upload_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_sha256 ON files(sha256);
CREATE INDEX IF NOT EXISTS idx_files_sha1 ON files(sha1);
CREATE INDEX IF NOT EXISTS idx_files_md5 ON files(md5);

-- ── Scan Jobs ──
CREATE TABLE IF NOT EXISTS scan_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    current_stage VARCHAR(64),
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    metadata_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_scan_jobs_file_id ON scan_jobs(file_id);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON scan_jobs(status);

-- ── Reports ──
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID UNIQUE NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    verdict VARCHAR(32) DEFAULT 'clean',
    summary TEXT,
    pe_info JSONB,
    elf_info JSONB,
    scoring_details JSONB,
    analysis_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_file_id ON reports(file_id);

-- ── Strings ──
CREATE TABLE IF NOT EXISTS strings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    value TEXT NOT NULL,
    encoding VARCHAR(16) DEFAULT 'ascii',
    "offset" INTEGER,
    length INTEGER NOT NULL,
    category VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_strings_file_id ON strings(file_id);

-- ── Indicators ──
CREATE TABLE IF NOT EXISTS indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_type VARCHAR(32) NOT NULL,
    value TEXT NOT NULL,
    reputation VARCHAR(32),
    enrichment_data JSONB,
    sample_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(indicator_type, value)
);

CREATE INDEX IF NOT EXISTS idx_indicators_type ON indicators(indicator_type);
CREATE INDEX IF NOT EXISTS idx_indicators_value ON indicators USING gin(value gin_trgm_ops);

-- ── File ↔ Indicator (M2M) ──
CREATE TABLE IF NOT EXISTS file_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    context VARCHAR(256),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id, indicator_id)
);

CREATE INDEX IF NOT EXISTS idx_file_indicators_file ON file_indicators(file_id);
CREATE INDEX IF NOT EXISTS idx_file_indicators_indicator ON file_indicators(indicator_id);

-- ── YARA Matches ──
CREATE TABLE IF NOT EXISTS yara_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    rule_name VARCHAR(256) NOT NULL,
    rule_namespace VARCHAR(256),
    rule_tags JSONB,
    severity VARCHAR(32) DEFAULT 'medium',
    description TEXT,
    matched_strings JSONB,
    score_contribution INTEGER DEFAULT 0,
    matched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_yara_matches_file_id ON yara_matches(file_id);
CREATE INDEX IF NOT EXISTS idx_yara_matches_rule ON yara_matches(rule_name);

-- ── Comments ──
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    author_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comments_file_id ON comments(file_id);

-- ── Tags ──
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#6b7280',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── File ↔ Tag (M2M) ──
CREATE TABLE IF NOT EXISTS file_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_file_tags_file ON file_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id);
