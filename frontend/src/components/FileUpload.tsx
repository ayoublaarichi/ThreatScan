"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, FileWarning, Loader2 } from "lucide-react";
import { api, type UploadResponse } from "@/lib/api";
import { useRouter } from "next/navigation";
import { formatBytes } from "@/lib/utils";

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function FileUpload() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      if (file.size > MAX_FILE_SIZE) {
        setError(`File too large (${formatBytes(file.size)}). Max: 50MB.`);
        return;
      }

      if (file.size === 0) {
        setError("Empty files cannot be analyzed.");
        return;
      }

      setSelectedFile(file);
      setIsUploading(true);

      try {
        const response: UploadResponse = await api.upload(file);

        if (response.status === "completed") {
          router.push(`/report/${response.sha256}`);
        } else {
          router.push(`/jobs/${response.job_id}`);
        }
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Upload failed. Please try again.";
        setError(message);
      } finally {
        setIsUploading(false);
      }
    },
    [router]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="w-full">
      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
          isDragging
            ? "border-brand-400 bg-brand-400/5"
            : "border-gray-700 hover:border-gray-600 bg-gray-900/50"
        } ${isUploading ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleInputChange}
          className="hidden"
          disabled={isUploading}
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-10 w-10 animate-spin text-brand-400" />
            <p className="text-lg font-medium text-gray-200">
              Uploading {selectedFile?.name}...
            </p>
            <p className="text-sm text-gray-500">
              {selectedFile && formatBytes(selectedFile.size)}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-10 w-10 text-gray-500" />
            <div>
              <p className="text-lg font-medium text-gray-200">
                Drop a file here or click to upload
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Maximum file size: 50MB — Static analysis only
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <FileWarning className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
