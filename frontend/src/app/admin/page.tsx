"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Settings,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import { cn, formatDate } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface JobItem {
  job_id: string;
  sha256: string;
  status: string;
  current_stage: string | null;
  progress: number;
  error_message: string | null;
  created_at: string;
}

export default function AdminPage() {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");

  const loadJobs = async () => {
    setLoading(true);
    try {
      const url = filter
        ? `${API_URL}/admin/jobs?status_filter=${filter}&limit=50`
        : `${API_URL}/admin/jobs?limit=50`;
      const res = await fetch(url);
      const data = await res.json();
      setJobs(data.jobs || []);
      setTotal(data.total || 0);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [filter]);

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-emerald-400" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-400" />;
      case "processing":
        return <Loader2 className="h-4 w-4 text-brand-400 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Settings className="h-6 w-6 text-brand-400" />
            Admin Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {total} total jobs
          </p>
        </div>
        <button
          onClick={loadJobs}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {["", "pending", "processing", "completed", "failed"].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
              filter === status
                ? "bg-brand-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            )}
          >
            {status || "All"}
          </button>
        ))}
      </div>

      {/* Jobs table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-900/50">
              <tr className="border-b border-gray-800">
                <th className="py-3 px-4 text-left text-xs text-gray-500 font-medium">Status</th>
                <th className="py-3 px-4 text-left text-xs text-gray-500 font-medium">SHA256</th>
                <th className="py-3 px-4 text-left text-xs text-gray-500 font-medium">Stage</th>
                <th className="py-3 px-4 text-left text-xs text-gray-500 font-medium">Progress</th>
                <th className="py-3 px-4 text-left text-xs text-gray-500 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.job_id}
                  className="border-b border-gray-800/50 hover:bg-gray-900/30"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {statusIcon(job.status)}
                      <span className="text-xs text-gray-400">{job.status}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <Link
                      href={`/report/${job.sha256}`}
                      className="font-mono text-xs text-brand-400 hover:underline"
                    >
                      {job.sha256.slice(0, 24)}…
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-xs text-gray-400">
                    {job.current_stage || "—"}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 rounded-full bg-gray-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-brand-400"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{job.progress}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-xs text-gray-500">
                    {formatDate(job.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs.length === 0 && (
            <div className="py-12 text-center text-sm text-gray-500">
              No jobs found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
