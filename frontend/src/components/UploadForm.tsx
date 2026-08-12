import { useState, useRef, type FormEvent, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeResume } from "../api/analyze";
import { addHistory } from "../lib/history";
import Button from "./ui/Button";
import Card from "./ui/Card";
import LoadingDashboard from "./LoadingDashboard";

const MAX_BYTES = 16 * 1024 * 1024;

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const accept = (f: File | null | undefined) => {
    if (!f) return;
    const ext = f.name.toLowerCase().split(".").pop();
    if (ext !== "pdf" && ext !== "docx" && ext !== "doc") {
      setError("Only PDF, DOC, and DOCX files are supported.");
      return;
    }
    if (f.size > MAX_BYTES) {
      setError("File is larger than 16 MB.");
      return;
    }
    setError(null);
    setFile(f);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    accept(e.dataTransfer.files?.[0]);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file.");
      return;
    }
    setError(null);
    setUploadProgress(0);
    setLoading(true);
    try {
      const data = await analyzeResume(file, jobDescription, setUploadProgress);
      addHistory(file.name, data);
      navigate("/results", { state: data });
    } catch (err: unknown) {
      const message =
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as Record<string, unknown>).response === "object"
          ? (err as { response: { data?: { error?: string } } }).response.data
              ?.error
          : null;
      setError(message ?? "Network error. Make sure the server is running.");
    } finally {
      setLoading(false);
    }
  };

  if (loading && file) {
    return (
      <LoadingDashboard
        uploadProgress={uploadProgress}
        fileName={file.name}
      />
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-brand-200">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-600" />
          AI-powered analysis
        </span>
        <h1 className="mt-4 font-display text-3xl font-semibold tracking-tight text-surface-900 sm:text-4xl">
          Score your resume in seconds.
        </h1>
        <p className="mt-3 text-base text-surface-700">
          Upload your CV — optionally paste a job description — and get a
          breakdown of skills, gaps, and what to improve.
        </p>
      </div>

      <Card className="p-6 sm:p-8">
        {error && (
          <div
            role="alert"
            aria-live="polite"
            className="mb-5 flex items-start justify-between gap-3 rounded-lg bg-danger-100 px-4 py-3 text-sm text-danger-500 ring-1 ring-danger-500/20"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-danger-500/70 transition-colors hover:text-danger-500"
              aria-label="Dismiss"
            >
              ×
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="mb-2 block text-sm font-medium text-surface-900">
              Resume
            </label>
            <div
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  inputRef.current?.click();
                }
              }}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              role="button"
              tabIndex={0}
              aria-label="Upload resume"
              className={`group cursor-pointer rounded-lg border-2 border-dashed px-6 py-10 text-center transition-all ${
                dragging
                  ? "border-brand-500 bg-brand-50"
                  : "border-surface-300 bg-surface-50 hover:border-brand-400 hover:bg-brand-50/40"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx,.doc"
                className="hidden"
                onChange={(e) => accept(e.target.files?.[0])}
              />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    className="h-8 w-8 text-brand-600"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <path d="M14 2v6h6" />
                  </svg>
                  <div className="text-left">
                    <div className="text-sm font-medium text-surface-900">
                      {file.name}
                    </div>
                    <div className="text-xs text-surface-700">
                      {formatBytes(file.size)} ·{" "}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFile(null);
                          if (inputRef.current) inputRef.current.value = "";
                        }}
                        className="text-brand-600 underline-offset-2 hover:underline"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="mx-auto mb-3 h-8 w-8 text-surface-700 transition-colors group-hover:text-brand-600"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <div className="text-sm font-medium text-surface-900">
                    Drop your resume here, or{" "}
                    <span className="text-brand-600">browse</span>
                  </div>
                  <div className="mt-1 text-xs text-surface-700">
                    PDF, DOC, or DOCX · up to 16 MB
                  </div>
                </>
              )}
            </div>
          </div>

          <div>
            <label
              htmlFor="jd"
              className="mb-2 flex items-center justify-between text-sm font-medium text-surface-900"
            >
              <span>Job description</span>
              <span className="text-xs font-normal text-surface-700">
                Optional — improves match scoring
              </span>
            </label>
            <textarea
              id="jd"
              rows={6}
              placeholder="Paste the job description here…"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              className="w-full resize-y rounded-lg border border-surface-300 bg-surface-0 px-4 py-3 text-sm text-surface-900 placeholder:text-surface-700/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </div>

          <Button
            type="submit"
            size="lg"
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <svg
                  className="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden
                >
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                <span>Analyzing…</span>
              </>
            ) : (
              <>Analyze resume</>
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
}
