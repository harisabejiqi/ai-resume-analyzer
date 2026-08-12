import { useEffect, useState } from "react";
import Card from "./ui/Card";

interface Props {
  uploadProgress: number;
  fileName: string;
}

const SCAN_MESSAGES = [
  "Extracting text from your resume…",
  "Identifying skills and experience…",
  "Detecting education and contact info…",
  "Comparing against the job description…",
  "Calculating your match score…",
  "Generating personalized suggestions…",
];

function Bar({ className = "" }: { className?: string }) {
  return (
    <div
      className={`h-3 animate-pulse rounded-md bg-surface-200 ${className}`}
    />
  );
}

function Chip({ width }: { width: string }) {
  return (
    <div
      className="h-6 animate-pulse rounded-full bg-surface-200"
      style={{ width }}
    />
  );
}

export default function LoadingDashboard({ uploadProgress, fileName }: Props) {
  const uploading = uploadProgress < 100;
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (uploading) return;
    const id = window.setInterval(() => {
      setMessageIndex((i) => (i + 1) % SCAN_MESSAGES.length);
    }, 1800);
    return () => window.clearInterval(id);
  }, [uploading]);

  return (
    <div className="space-y-6">
      <Card accent="info" className="p-6">
        <div className="flex items-center gap-3">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="h-6 w-6 shrink-0 text-brand-600"
            aria-hidden
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <path d="M14 2v6h6" />
          </svg>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-surface-900">
              {fileName}
            </div>
            <div
              key={uploading ? "upload" : messageIndex}
              aria-live="polite"
              className="mt-0.5 animate-[fadeIn_400ms_ease-out] text-xs text-surface-700"
            >
              {uploading
                ? `Uploading… ${uploadProgress}%`
                : SCAN_MESSAGES[messageIndex]}
            </div>
          </div>
        </div>

        <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-200">
          {uploading ? (
            <div
              className="h-full rounded-full bg-brand-500 transition-[width] duration-200 ease-out"
              style={{ width: `${uploadProgress}%` }}
              role="progressbar"
              aria-valuenow={uploadProgress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Upload progress"
            />
          ) : (
            <div
              className="h-full w-1/3 animate-[indeterminate_1.4s_ease-in-out_infinite] rounded-full bg-brand-500"
              role="progressbar"
              aria-label="Analyzing resume"
            />
          )}
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <aside className="space-y-6 lg:col-span-1">
          <Card>
            <Bar className="mx-auto h-3 w-24" />
            <div className="mx-auto mt-4 h-44 w-44 animate-pulse rounded-full bg-surface-200" />
            <Bar className="mx-auto mt-4 h-3 w-32" />
          </Card>
          <Card>
            <Bar className="h-4 w-40" />
            <div className="mt-5 space-y-4">
              <div>
                <Bar className="h-2 w-28" />
                <Bar className="mt-2 h-2 w-full" />
              </div>
              <div>
                <Bar className="h-2 w-20" />
                <Bar className="mt-2 h-2 w-full" />
              </div>
              <div>
                <Bar className="h-2 w-24" />
                <Bar className="mt-2 h-2 w-full" />
              </div>
              <div>
                <Bar className="h-2 w-32" />
                <Bar className="mt-2 h-2 w-full" />
              </div>
            </div>
          </Card>
        </aside>

        <div className="space-y-6 lg:col-span-2">
          <Card>
            <Bar className="h-4 w-36" />
            <div className="mt-5 space-y-3">
              <Bar className="h-3 w-full" />
              <Bar className="h-3 w-11/12" />
              <Bar className="h-3 w-4/5" />
            </div>
          </Card>
          <Card>
            <Bar className="h-4 w-32" />
            <div className="mt-5 grid grid-cols-2 gap-3">
              <Bar className="h-3" />
              <Bar className="h-3" />
              <Bar className="h-3" />
              <Bar className="h-3" />
            </div>
          </Card>
          <Card>
            <Bar className="h-4 w-28" />
            <div className="mt-5 flex flex-wrap gap-2">
              <Chip width="72px" />
              <Chip width="96px" />
              <Chip width="64px" />
              <Chip width="84px" />
              <Chip width="56px" />
              <Chip width="100px" />
              <Chip width="76px" />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
