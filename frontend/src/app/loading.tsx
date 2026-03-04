"use client";

import { Shield } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center">
      <div className="relative">
        <Shield className="h-16 w-16 animate-pulse text-brand-400" />
        <div className="absolute inset-0 h-16 w-16 animate-ping rounded-full border-2 border-brand-400 opacity-20" />
      </div>
      <p className="mt-6 text-sm text-slate-400">Loading…</p>
    </div>
  );
}
