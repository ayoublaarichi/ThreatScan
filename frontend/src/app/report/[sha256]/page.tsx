"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  Hash,
  FileText,
  Globe,
  Link2,
  MessageSquare,
  Tag,
  Loader2,
  AlertTriangle,
  Copy,
  Check,
} from "lucide-react";
import { api, type ReportResponse } from "@/lib/api";
import {
  formatBytes,
  formatDate,
  getVerdictColor,
  getVerdictBg,
  getSeverityColor,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { Tabs } from "@/components/Tabs";

type TabKey = "overview" | "details" | "strings" | "iocs" | "relations" | "community";

export default function ReportPage() {
  const params = useParams();
  const sha256 = params.sha256 as string;

  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Comment form
  const [commentText, setCommentText] = useState("");
  const [commentAuthor, setCommentAuthor] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  // Tag form
  const [tagName, setTagName] = useState("");
  const [submittingTag, setSubmittingTag] = useState(false);

  const loadReport = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getReport(sha256);
      setReport(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load report");
    } finally {
      setLoading(false);
    }
  }, [sha256]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleAddComment = async () => {
    if (!commentText.trim()) return;
    setSubmittingComment(true);
    try {
      await api.addComment(sha256, commentText, commentAuthor || undefined);
      setCommentText("");
      setCommentAuthor("");
      loadReport();
    } catch {
      /* ignore */
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleAddTag = async () => {
    if (!tagName.trim()) return;
    setSubmittingTag(true);
    try {
      await api.addTag(sha256, tagName);
      setTagName("");
      loadReport();
    } catch {
      /* ignore */
    } finally {
      setSubmittingTag(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <AlertTriangle className="h-12 w-12 text-amber-400" />
        <h2 className="text-xl font-semibold text-white">Report Not Found</h2>
        <p className="text-gray-400">{error || "The analysis may still be in progress."}</p>
        <Link href="/" className="text-brand-400 hover:underline text-sm">
          Back to home
        </Link>
      </div>
    );
  }

  const { file, score, verdict, yara_matches, indicators, tags, comments } = report;

  const tabDefs: { key: TabKey; label: string; count?: number }[] = [
    { key: "overview", label: "Overview" },
    { key: "details", label: "Details" },
    { key: "strings", label: "Strings" },
    { key: "iocs", label: "IOCs", count: indicators.length },
    { key: "relations", label: "Relations" },
    { key: "community", label: "Community", count: comments.length },
  ];

  const CopyBtn = ({ text, field }: { text: string; field: string }) => (
    <button
      onClick={() => copyToClipboard(text, field)}
      className="ml-2 text-gray-500 hover:text-gray-300"
      title="Copy"
    >
      {copiedField === field ? (
        <Check className="h-3.5 w-3.5 text-emerald-400" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
    </button>
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Shield className={cn("h-6 w-6", getVerdictColor(verdict))} />
            <h1 className="text-2xl font-bold text-white truncate">
              {file.file_name}
            </h1>
          </div>

          {/* Hash badges */}
          <div className="flex flex-wrap gap-2 mt-3">
            <HashBadge label="SHA256" value={file.sha256} copyBtn={<CopyBtn text={file.sha256} field="sha256" />} />
            {file.sha1 && <HashBadge label="SHA1" value={file.sha1} copyBtn={<CopyBtn text={file.sha1} field="sha1" />} />}
            {file.md5 && <HashBadge label="MD5" value={file.md5} copyBtn={<CopyBtn text={file.md5} field="md5" />} />}
          </div>

          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {tags.map((tag) => (
                <span
                  key={tag.id}
                  className="rounded-full bg-gray-800 px-3 py-0.5 text-xs text-gray-300 border border-gray-700"
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <ScoreGauge score={score} verdict={verdict} size="lg" />
      </div>

      {/* Summary */}
      {report.summary && (
        <div
          className={cn(
            "mb-6 rounded-lg border p-4 text-sm",
            getVerdictBg(verdict),
            getVerdictColor(verdict)
          )}
        >
          {report.summary}
        </div>
      )}

      {/* Tabs */}
      <Tabs
        tabs={tabDefs}
        activeTab={activeTab}
        onTabChange={(t) => setActiveTab(t as TabKey)}
      />

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === "overview" && (
          <OverviewTab report={report} />
        )}
        {activeTab === "details" && (
          <DetailsTab report={report} />
        )}
        {activeTab === "strings" && (
          <StringsTab sha256={sha256} />
        )}
        {activeTab === "iocs" && (
          <IOCsTab indicators={indicators} />
        )}
        {activeTab === "relations" && (
          <RelationsTab sha256={sha256} />
        )}
        {activeTab === "community" && (
          <CommunityTab
            comments={comments}
            commentText={commentText}
            commentAuthor={commentAuthor}
            tagName={tagName}
            submittingComment={submittingComment}
            submittingTag={submittingTag}
            onCommentTextChange={setCommentText}
            onCommentAuthorChange={setCommentAuthor}
            onTagNameChange={setTagName}
            onAddComment={handleAddComment}
            onAddTag={handleAddTag}
          />
        )}
      </div>
    </div>
  );
}

// ── Subcomponents ──

function HashBadge({
  label,
  value,
  copyBtn,
}: {
  label: string;
  value: string;
  copyBtn: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-1 rounded bg-gray-900 px-2 py-1 text-xs">
      <span className="text-gray-500">{label}:</span>
      <code className="font-mono text-gray-300">{value}</code>
      {copyBtn}
    </div>
  );
}

function OverviewTab({ report }: { report: ReportResponse }) {
  const { file, score, verdict, yara_matches, indicators, scoring_details } = report;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* File Info */}
      <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <FileText className="h-4 w-4" /> File Information
        </h3>
        <dl className="space-y-3 text-sm">
          <InfoRow label="File Name" value={file.file_name} />
          <InfoRow label="Size" value={formatBytes(file.file_size)} />
          <InfoRow label="MIME Type" value={file.mime_type || "unknown"} />
          <InfoRow label="Magic" value={file.magic_description || "unknown"} />
          <InfoRow label="Entropy" value={file.entropy?.toFixed(4) || "N/A"} />
          <InfoRow label="First Seen" value={formatDate(file.first_seen)} />
          <InfoRow label="Last Seen" value={formatDate(file.last_seen)} />
          <InfoRow label="Upload Count" value={String(file.upload_count)} />
        </dl>
      </div>

      {/* Scoring */}
      <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Shield className="h-4 w-4" /> Scoring Details
        </h3>
        {scoring_details ? (
          <div className="space-y-3">
            {Object.entries(scoring_details).map(([category, items]) => (
              items.length > 0 && (
                <div key={category}>
                  <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                    {category.replace(/_/g, " ")}
                  </h4>
                  <ul className="space-y-1">
                    {items.map((item: string, i: number) => (
                      <li key={i} className="text-xs text-gray-400">
                        • {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No scoring details available.</p>
        )}
      </div>

      {/* YARA Matches */}
      {yara_matches.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> YARA Matches ({yara_matches.length})
          </h3>
          <div className="space-y-3">
            {yara_matches.map((match, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg border border-gray-800 bg-gray-950 p-3"
              >
                <span
                  className={cn(
                    "shrink-0 rounded px-2 py-0.5 text-xs font-medium",
                    getSeverityColor(match.severity)
                  )}
                >
                  {match.severity}
                </span>
                <div className="min-w-0">
                  <p className="font-mono text-sm text-white">{match.rule_name}</p>
                  {match.description && (
                    <p className="text-xs text-gray-400 mt-1">{match.description}</p>
                  )}
                  {match.rule_tags && match.rule_tags.length > 0 && (
                    <div className="flex gap-1 mt-1">
                      {match.rule_tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded bg-gray-800 px-1.5 py-0.5 text-xs text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="ml-auto text-xs text-gray-500">
                  +{match.score_contribution}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailsTab({ report }: { report: ReportResponse }) {
  const { pe_info, elf_info, analysis_duration_ms } = report;

  return (
    <div className="space-y-6">
      {analysis_duration_ms && (
        <p className="text-sm text-gray-500">
          Analysis completed in {analysis_duration_ms}ms
        </p>
      )}

      {pe_info && (
        <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">
            PE Header Information
          </h3>
          <dl className="space-y-2 text-sm">
            <InfoRow label="Machine" value={String(pe_info.machine)} />
            <InfoRow label="Sections" value={String(pe_info.number_of_sections)} />
            <InfoRow label="Entry Point" value={String(pe_info.entry_point)} />
            <InfoRow label="Image Base" value={String(pe_info.image_base)} />
          </dl>

          {pe_info.sections && (
            <div className="mt-4">
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                Sections
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="py-2 pr-4 text-left text-gray-500">Name</th>
                      <th className="py-2 pr-4 text-left text-gray-500">Virtual Size</th>
                      <th className="py-2 pr-4 text-left text-gray-500">Raw Size</th>
                      <th className="py-2 pr-4 text-left text-gray-500">Entropy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(pe_info.sections as Array<Record<string, unknown>>).map(
                      (section, i) => (
                        <tr key={i} className="border-b border-gray-800/50">
                          <td className="py-2 pr-4 font-mono text-gray-300">
                            {String(section.name)}
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {formatBytes(section.virtual_size as number)}
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {formatBytes(section.raw_size as number)}
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {String(section.entropy)}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {!pe_info && !elf_info && (
        <p className="text-sm text-gray-500">
          No additional binary details available for this file type.
        </p>
      )}
    </div>
  );
}

function StringsTab({ sha256 }: { sha256: string }) {
  // In a full implementation, this would fetch strings via a dedicated endpoint
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
      <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
        <FileText className="h-4 w-4" /> Extracted Strings
      </h3>
      <p className="text-sm text-gray-500">
        Strings are extracted during analysis. View the full report for details.
      </p>
      <p className="text-xs text-gray-600 mt-2">
        Endpoint: <code className="font-mono">/report/{sha256}/strings</code>
      </p>
    </div>
  );
}

function IOCsTab({ indicators }: { indicators: ReportResponse["indicators"] }) {
  const grouped = indicators.reduce(
    (acc, ind) => {
      const type = ind.indicator_type;
      if (!acc[type]) acc[type] = [];
      acc[type].push(ind);
      return acc;
    },
    {} as Record<string, typeof indicators>
  );

  if (indicators.length === 0) {
    return <p className="text-sm text-gray-500">No indicators of compromise found.</p>;
  }

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type} className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Globe className="h-4 w-4" />
            {type.toUpperCase()}s ({items.length})
          </h3>
          <div className="space-y-1">
            {items.map((ind, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded px-3 py-2 text-sm hover:bg-gray-800/50"
              >
                <Link
                  href={`/indicator/${ind.indicator_type}/${encodeURIComponent(ind.value)}`}
                  className="font-mono text-brand-400 hover:underline truncate"
                >
                  {ind.value}
                </Link>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  {ind.reputation && (
                    <span className={cn("text-xs", getVerdictColor(ind.reputation))}>
                      {ind.reputation}
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    {ind.sample_count} sample(s)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function RelationsTab({ sha256 }: { sha256: string }) {
  const [relations, setRelations] = useState<{
    indicators: ReportResponse["indicators"];
    related_files: Array<{ sha256: string; file_name: string; mime_type: string | null }>;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getRelations(sha256)
      .then(setRelations)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [sha256]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
      </div>
    );
  }

  if (!relations) {
    return <p className="text-sm text-gray-500">Could not load relations.</p>;
  }

  return (
    <div className="space-y-6">
      {relations.related_files.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Link2 className="h-4 w-4" />
            Related Files ({relations.related_files.length})
          </h3>
          <div className="space-y-2">
            {relations.related_files.map((f) => (
              <Link
                key={f.sha256}
                href={`/report/${f.sha256}`}
                className="flex items-center gap-3 rounded px-3 py-2 text-sm hover:bg-gray-800/50"
              >
                <FileText className="h-4 w-4 text-gray-500 shrink-0" />
                <span className="text-gray-300 truncate">{f.file_name}</span>
                <code className="ml-auto text-xs text-gray-500 font-mono">
                  {f.sha256.slice(0, 16)}…
                </code>
              </Link>
            ))}
          </div>
        </div>
      )}

      {relations.related_files.length === 0 && (
        <p className="text-sm text-gray-500">No related files found.</p>
      )}
    </div>
  );
}

function CommunityTab({
  comments,
  commentText,
  commentAuthor,
  tagName,
  submittingComment,
  submittingTag,
  onCommentTextChange,
  onCommentAuthorChange,
  onTagNameChange,
  onAddComment,
  onAddTag,
}: {
  comments: ReportResponse["comments"];
  commentText: string;
  commentAuthor: string;
  tagName: string;
  submittingComment: boolean;
  submittingTag: boolean;
  onCommentTextChange: (v: string) => void;
  onCommentAuthorChange: (v: string) => void;
  onTagNameChange: (v: string) => void;
  onAddComment: () => void;
  onAddTag: () => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* Comments */}
      <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Comments ({comments.length})
        </h3>

        {/* Add comment form */}
        <div className="space-y-2 mb-4">
          <input
            type="text"
            value={commentAuthor}
            onChange={(e) => onCommentAuthorChange(e.target.value)}
            placeholder="Your name (optional)"
            className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-brand-500 focus:outline-none"
          />
          <textarea
            value={commentText}
            onChange={(e) => onCommentTextChange(e.target.value)}
            placeholder="Add a comment..."
            rows={3}
            className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-brand-500 focus:outline-none resize-none"
          />
          <button
            onClick={onAddComment}
            disabled={submittingComment || !commentText.trim()}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submittingComment ? "Posting..." : "Post Comment"}
          </button>
        </div>

        {/* Comment list */}
        <div className="space-y-3">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="rounded-lg border border-gray-800 bg-gray-950 p-3"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-400">
                  {comment.author_name || "Anonymous"}
                </span>
                <span className="text-xs text-gray-600">
                  {formatDate(comment.created_at)}
                </span>
              </div>
              <p className="text-sm text-gray-300">{comment.content}</p>
            </div>
          ))}
          {comments.length === 0 && (
            <p className="text-sm text-gray-600">No comments yet.</p>
          )}
        </div>
      </div>

      {/* Tags */}
      <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Tag className="h-4 w-4" />
          Tags
        </h3>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={tagName}
            onChange={(e) => onTagNameChange(e.target.value)}
            placeholder="Add tag..."
            className="flex-1 rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-brand-500 focus:outline-none"
          />
          <button
            onClick={onAddTag}
            disabled={submittingTag || !tagName.trim()}
            className="rounded-lg bg-gray-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-gray-500 shrink-0">{label}</dt>
      <dd className="text-gray-300 text-right truncate font-mono">{value}</dd>
    </div>
  );
}
