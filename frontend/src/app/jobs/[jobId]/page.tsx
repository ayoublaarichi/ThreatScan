"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import { api, type JobStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const STAGES = [
  { key: "queued", label: "Queued" },
  { key: "ingestion", label: "File Ingestion" },
  { key: "hashing", label: "Hash Computation" },
  { key: "metadata", label: "Metadata Analysis" },
  { key: "strings", label: "String Extraction" },
  { key: "ioc_extraction", label: "IOC Extraction" },
  { key: "yara_scan", label: "YARA Scanning" },
  { key: "scoring", label: "Scoring" },
  { key: "report_generation", label: "Report Generation" },
  { key: "completed", label: "Completed" },
];

export default function JobPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollJob = useCallback(async () => {
    try {
      const data = await api.getJob(jobId);
      setJob(data);

      if (data.status === "completed") {
        // Redirect to report
        setTimeout(() => {
          router.push(`/report/${data.sha256}`);
        }, 1500);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load job status");
    }
  }, [jobId, router]);

  useEffect(() => {
    pollJob();
    const interval = setInterval(() => {
      pollJob();
    }, 2000);
    return () => clearInterval(interval);
  }, [pollJob]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <XCircle className="h-12 w-12 text-red-400" />
        <h2 className="text-xl font-semibold text-white">Job Not Found</h2>
        <p className="text-gray-400">{error}</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
      </div>
    );
  }

  const currentStageIndex = STAGES.findIndex((s) => s.key === job.current_stage);

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <div className="text-center mb-8">
        {job.status === "completed" ? (
          <CheckCircle className="h-12 w-12 text-emerald-400 mx-auto mb-4" />
        ) : job.status === "failed" ? (
          <XCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
        ) : (
          <Loader2 className="h-12 w-12 animate-spin text-brand-400 mx-auto mb-4" />
        )}

        <h1 className="text-2xl font-bold text-white">
          {job.status === "completed"
            ? "Analysis Complete"
            : job.status === "failed"
            ? "Analysis Failed"
            : "Analyzing File..."}
        </h1>
        <p className="mt-2 text-sm text-gray-400 font-mono">{job.sha256}</p>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          <span className="text-sm text-gray-400">Progress</span>
          <span className="text-sm text-gray-400">{job.progress}%</span>
        </div>
        <div className="h-2 rounded-full bg-gray-800 overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              job.status === "failed" ? "bg-red-400" :
              job.status === "completed" ? "bg-emerald-400" : "bg-brand-400"
            )}
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>

      {/* Stages */}
      <div className="space-y-2">
        {STAGES.map((stage, i) => {
          const isComplete = i < currentStageIndex || job.status === "completed";
          const isCurrent = stage.key === job.current_stage && job.status === "processing";
          const isPending = i > currentStageIndex;

          return (
            <div
              key={stage.key}
              className={cn(
                "flex items-center gap-3 rounded-lg border px-4 py-3 text-sm transition-all",
                isComplete
                  ? "border-emerald-400/20 bg-emerald-400/5 text-emerald-400"
                  : isCurrent
                  ? "border-brand-400/20 bg-brand-400/5 text-brand-400"
                  : "border-gray-800 bg-gray-900/30 text-gray-600"
              )}
            >
              {isComplete ? (
                <CheckCircle className="h-4 w-4 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
              ) : (
                <Clock className="h-4 w-4 shrink-0" />
              )}
              {stage.label}
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {job.status === "failed" && job.error_message && (
        <div className="mt-6 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          <strong>Error:</strong> {job.error_message}
        </div>
      )}

      {/* Redirect notice */}
      {job.status === "completed" && (
        <p className="mt-6 text-center text-sm text-gray-500">
          Redirecting to report...
        </p>
      )}
    </div>
  );
}
