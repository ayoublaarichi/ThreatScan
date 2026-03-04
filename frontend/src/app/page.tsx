import { FileUpload } from "@/components/FileUpload";
import { Shield, Search, FileText, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
      {/* Hero */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-6">
          <div className="rounded-2xl bg-brand-400/10 p-4">
            <Shield className="h-12 w-12 text-brand-400" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-white sm:text-5xl">
          Threat<span className="text-brand-400">Scan</span>
        </h1>
        <p className="mt-4 text-lg text-gray-400 max-w-2xl mx-auto">
          Upload suspicious files for safe static analysis. Extract indicators,
          run YARA rules, and get a comprehensive threat report.
        </p>
      </div>

      {/* Upload */}
      <FileUpload />

      {/* Features */}
      <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3">
        <FeatureCard
          icon={<Search className="h-6 w-6 text-brand-400" />}
          title="IOC Extraction"
          description="Automatically extract domains, IPs, URLs, and email addresses from uploaded files."
        />
        <FeatureCard
          icon={<FileText className="h-6 w-6 text-brand-400" />}
          title="YARA Scanning"
          description="Match files against curated YARA rules to detect known malware families and techniques."
        />
        <FeatureCard
          icon={<Zap className="h-6 w-6 text-brand-400" />}
          title="Threat Scoring"
          description="Automated scoring engine rates files as clean, suspicious, or malicious."
        />
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      <div className="mb-3">{icon}</div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="mt-1 text-sm text-gray-400">{description}</p>
    </div>
  );
}
