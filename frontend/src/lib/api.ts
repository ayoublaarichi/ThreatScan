/**
 * ThreatScan — API Client
 *
 * Type-safe HTTP client for the ThreatScan FastAPI backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ──

export interface HealthResponse {
  status: string;
  version: string;
  services: Record<string, string>;
}

export interface UploadResponse {
  job_id: string;
  sha256: string;
  file_name: string;
  status: string;
  message: string;
}

export interface JobStatus {
  job_id: string;
  sha256: string;
  status: "pending" | "processing" | "completed" | "failed";
  current_stage: string | null;
  progress: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface FileInfo {
  sha256: string;
  sha1: string | null;
  md5: string | null;
  file_name: string;
  file_size: number;
  mime_type: string | null;
  magic_description: string | null;
  entropy: number | null;
  upload_count: number;
  first_seen: string;
  last_seen: string;
}

export interface YaraMatch {
  rule_name: string;
  rule_namespace: string | null;
  rule_tags: string[] | null;
  severity: string;
  description: string | null;
  matched_strings: Array<{
    offset: number;
    identifier: string;
    data: string;
  }> | null;
  score_contribution: number;
}

export interface Indicator {
  indicator_type: string;
  value: string;
  reputation: string | null;
  context: string | null;
  sample_count: number;
  first_seen: string | null;
  last_seen: string | null;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export interface Comment {
  id: string;
  content: string;
  author_name: string | null;
  created_at: string;
}

export interface ReportResponse {
  file: FileInfo;
  score: number;
  verdict: "clean" | "suspicious" | "malicious";
  summary: string | null;
  pe_info: Record<string, unknown> | null;
  elf_info: Record<string, unknown> | null;
  scoring_details: Record<string, string[]> | null;
  yara_matches: YaraMatch[];
  indicators: Indicator[];
  tags: Tag[];
  comments: Comment[];
  analysis_duration_ms: number | null;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  result_type: "file" | "indicator";
  sha256: string | null;
  indicator_type: string | null;
  indicator_value: string | null;
  file_name: string | null;
  verdict: string | null;
  score: number | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface RelationsResponse {
  sha256: string;
  indicators: Indicator[];
  related_files: FileInfo[];
}

export interface IndicatorPivotResponse {
  indicator: Indicator;
  files: FileInfo[];
}

// ── API Functions ──

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || "API request failed");
  }

  return res.json();
}

export const api = {
  /** Health check */
  health: () => apiFetch<HealthResponse>("/health"),

  /** Upload a file for analysis */
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<UploadResponse>("/upload", {
      method: "POST",
      body: formData,
    });
  },

  /** Get job status */
  getJob: (jobId: string) => apiFetch<JobStatus>(`/jobs/${jobId}`),

  /** Get analysis report */
  getReport: (sha256: string) => apiFetch<ReportResponse>(`/report/${sha256}`),

  /** Get related indicators and files */
  getRelations: (sha256: string) =>
    apiFetch<RelationsResponse>(`/report/${sha256}/relations`),

  /** Search files and indicators */
  search: (query: string) =>
    apiFetch<SearchResponse>(`/search?q=${encodeURIComponent(query)}`),

  /** Pivot on indicator */
  getIndicator: (type: string, value: string) =>
    apiFetch<IndicatorPivotResponse>(
      `/indicator/${type}/${encodeURIComponent(value)}`
    ),

  /** Add comment to report */
  addComment: (sha256: string, content: string, authorName?: string) =>
    apiFetch<Comment>(`/report/${sha256}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, author_name: authorName }),
    }),

  /** Add tag to report */
  addTag: (sha256: string, name: string) =>
    apiFetch<Tag>(`/report/${sha256}/tag`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),
};
