/**
 * ThreatScan — Utility functions
 */

import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncateHash(hash: string, length: number = 16): string {
  if (hash.length <= length) return hash;
  return `${hash.slice(0, length)}…`;
}

export function getVerdictColor(verdict: string): string {
  switch (verdict) {
    case "clean":
      return "text-emerald-400";
    case "suspicious":
      return "text-amber-400";
    case "malicious":
      return "text-red-400";
    default:
      return "text-gray-400";
  }
}

export function getVerdictBg(verdict: string): string {
  switch (verdict) {
    case "clean":
      return "bg-emerald-400/10 border-emerald-400/20";
    case "suspicious":
      return "bg-amber-400/10 border-amber-400/20";
    case "malicious":
      return "bg-red-400/10 border-red-400/20";
    default:
      return "bg-gray-400/10 border-gray-400/20";
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-red-400 bg-red-400/10";
    case "high":
      return "text-orange-400 bg-orange-400/10";
    case "medium":
      return "text-amber-400 bg-amber-400/10";
    case "low":
      return "text-blue-400 bg-blue-400/10";
    default:
      return "text-gray-400 bg-gray-400/10";
  }
}

export function getScoreColor(score: number): string {
  if (score >= 60) return "text-red-400";
  if (score >= 25) return "text-amber-400";
  return "text-emerald-400";
}
