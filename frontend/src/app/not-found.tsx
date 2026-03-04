import Link from "next/link";
import { Shield, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-32 gap-4">
      <Shield className="h-16 w-16 text-gray-700" />
      <h2 className="text-2xl font-bold text-white">404 — Not Found</h2>
      <p className="text-gray-400">The page you&apos;re looking for doesn&apos;t exist.</p>
      <Link
        href="/"
        className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
      >
        <Home className="h-4 w-4" />
        Back to Home
      </Link>
    </div>
  );
}
