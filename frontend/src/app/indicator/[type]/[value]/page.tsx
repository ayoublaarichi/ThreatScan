"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Globe, FileText, Loader2, AlertTriangle } from "lucide-react";
import { api, type IndicatorPivotResponse } from "@/lib/api";
import { formatBytes, formatDate, getVerdictColor, cn } from "@/lib/utils";

export default function IndicatorPage() {
  const params = useParams();
  const indicatorType = params.type as string;
  const value = decodeURIComponent(params.value as string);

  const [data, setData] = useState<IndicatorPivotResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .getIndicator(indicatorType, value)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [indicatorType, value]);

  if (loading) {
    return (
      <div className="flex justify-center py-32">
        <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <AlertTriangle className="h-12 w-12 text-amber-400" />
        <h2 className="text-xl font-semibold text-white">Indicator Not Found</h2>
        <p className="text-gray-400">{error}</p>
      </div>
    );
  }

  const { indicator, files } = data;

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Globe className="h-6 w-6 text-brand-400" />
          <span className="rounded bg-gray-800 px-2 py-0.5 text-xs font-medium text-gray-400 uppercase">
            {indicator.indicator_type}
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white font-mono break-all">
          {indicator.value}
        </h1>
        <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
          {indicator.reputation && (
            <span className={cn("font-medium", getVerdictColor(indicator.reputation))}>
              Reputation: {indicator.reputation}
            </span>
          )}
          <span>{indicator.sample_count} related sample(s)</span>
          {indicator.first_seen && (
            <span>First seen: {formatDate(indicator.first_seen)}</span>
          )}
        </div>
      </div>

      {/* Related files */}
      <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">
          Related Samples ({files.length})
        </h3>

        {files.length > 0 ? (
          <div className="space-y-2">
            {files.map((file) => (
              <Link
                key={file.sha256}
                href={`/report/${file.sha256}`}
                className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-950 p-4 hover:bg-gray-900 transition-colors"
              >
                <FileText className="h-5 w-5 text-gray-500 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-white truncate">{file.file_name}</p>
                  <p className="text-xs text-gray-500 font-mono mt-0.5">
                    {file.sha256}
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-xs text-gray-400">
                    {formatBytes(file.file_size)}
                  </p>
                  <p className="text-xs text-gray-500">{file.mime_type}</p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No related samples found.</p>
        )}
      </div>
    </div>
  );
}
