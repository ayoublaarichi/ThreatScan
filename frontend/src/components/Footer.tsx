import { Shield } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-gray-800 bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-brand-400" />
            <span className="text-sm text-gray-400">
              ThreatScan — Open-source threat intelligence platform
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>Static analysis only — no dynamic execution</span>
            <span>•</span>
            <span>MIT License</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
