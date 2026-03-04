"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Search, FileText, Globe, Loader2 } from "lucide-react";
import { api, type SearchResponse, type SearchResult } from "@/lib/api";
import { cn, getVerdictColor, truncateHash } from "@/lib/utils";

export default function SearchPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";

  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    api
      .search(query)
      .then(setResults)
      .catch(() => setResults(null))
      .finally(() => setLoading(false));
  }, [query]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Search className="h-6 w-6 text-brand-400" />
          Search Results
        </h1>
        <p className="mt-2 text-sm text-gray-400">
          Query: <code className="font-mono text-gray-300">{query}</code>
        </p>
      </div>

      {loading && (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
        </div>
      )}

      {!loading && results && (
        <>
          <p className="mb-4 text-sm text-gray-500">
            {results.total} result(s) found
          </p>
          <div className="space-y-2">
            {results.results.map((result, i) => (
              <SearchResultCard key={i} result={result} />
            ))}
          </div>
          {results.total === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-500">No results found for this query.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SearchResultCard({ result }: { result: SearchResult }) {
  if (result.result_type === "file") {
    return (
      <Link
        href={`/report/${result.sha256}`}
        className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-900/50 p-4 hover:bg-gray-900/80 transition-colors"
      >
        <FileText className="h-5 w-5 text-gray-500 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-sm text-white truncate">{result.file_name}</p>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            {result.sha256}
          </p>
        </div>
        {result.verdict && (
          <span
            className={cn(
              "shrink-0 text-xs font-medium uppercase",
              getVerdictColor(result.verdict)
            )}
          >
            {result.verdict}
          </span>
        )}
        {result.score !== null && result.score !== undefined && (
          <span className="shrink-0 text-xs text-gray-500">
            Score: {result.score}
          </span>
        )}
      </Link>
    );
  }

  return (
    <Link
      href={`/indicator/${result.indicator_type}/${encodeURIComponent(result.indicator_value || "")}`}
      className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-900/50 p-4 hover:bg-gray-900/80 transition-colors"
    >
      <Globe className="h-5 w-5 text-gray-500 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-brand-400 font-mono truncate">
          {result.indicator_value}
        </p>
        <p className="text-xs text-gray-500 mt-0.5">
          Type: {result.indicator_type}
        </p>
      </div>
    </Link>
  );
}
