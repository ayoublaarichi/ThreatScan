"use client";

import { useCallback, useEffect, useState } from "react";
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
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>("");
  const [adminPassword, setAdminPassword] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    if (!adminPassword) return;

    setLoading(true);
    try {
      const url = filter
        ? `${API_URL}/admin/jobs?status_filter=${filter}&limit=50`
        : `${API_URL}/admin/jobs?limit=50`;

      const res = await fetch(url, {
        headers: {
          "X-Admin-Password": adminPassword,
        },
      });

      if (res.status === 401) {
        setAuthError("Invalid admin password");
        localStorage.removeItem("threatscan_admin_password");
        setAdminPassword("");
        return;
      }

      if (!res.ok) {
        throw new Error("Failed to load admin jobs");
      }

      const data = await res.json();
      setJobs(data.jobs || []);
      setTotal(data.total || 0);
      setAuthError(null);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [adminPassword, filter]);

  const handleUnlock = () => {
    if (!passwordInput.trim()) return;

    localStorage.setItem("threatscan_admin_password", passwordInput);
    setAdminPassword(passwordInput);
    setAuthError(null);
  };

  const handleLogout = () => {
    localStorage.removeItem("threatscan_admin_password");
    setAdminPassword("");
    setPasswordInput("");
    setJobs([]);
    setTotal(0);
  };

  useEffect(() => {
    const savedPassword = localStorage.getItem("threatscan_admin_password");
    if (savedPassword) {
      setAdminPassword(savedPassword);
      setPasswordInput(savedPassword);
    }
  }, []);

  useEffect(() => {
    if (adminPassword) {
      loadJobs();
    }
  }, [adminPassword, loadJobs]);

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

  if (!adminPassword) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-gray-800 bg-gray-900/40 p-6">
          <h1 className="text-lg font-semibold text-white">Admin Access</h1>
          <p className="mt-2 text-sm text-gray-400">
            Enter the admin password to continue.
          </p>
          <input
            type="password"
            value={passwordInput}
            onChange={(event) => setPasswordInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                handleUnlock();
              }
            }}
            className="mt-4 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-200 outline-none focus:border-brand-500"
            placeholder="Admin password"
          />
          <button
            onClick={handleUnlock}
            className="mt-3 w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
          >
            Unlock Admin
          </button>
          {authError && (
            <p className="mt-3 text-xs text-red-400">{authError}</p>
          )}
        </div>
      </div>
    );
  }

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
        <div className="flex items-center gap-2">
          <button
            onClick={loadJobs}
            className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={handleLogout}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
          >
            Lock
          </button>
        </div>
      </div>
      {authError && (
        <div className="mb-4 rounded-lg border border-red-900/50 bg-red-950/20 px-3 py-2 text-xs text-red-300">
          {authError}
        </div>
      )}

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
