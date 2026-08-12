import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  getHistory,
  removeHistory,
  clearHistory,
  type HistoryEntry,
} from "../lib/history";
import Card from "./ui/Card";
import Button from "./ui/Button";

const RING = 132;

function scoreColor(score: number) {
  if (score >= 70) return "text-success-500";
  if (score >= 40) return "text-warning-500";
  return "text-danger-500";
}

function MiniRing({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const offset = RING - (RING * pct) / 100;
  return (
    <div className="relative h-14 w-14 shrink-0">
      <svg viewBox="0 0 50 50" className="h-full w-full -rotate-90">
        <circle
          cx="25"
          cy="25"
          r="21"
          fill="none"
          strokeWidth="5"
          className="stroke-surface-200"
        />
        <circle
          cx="25"
          cy="25"
          r="21"
          fill="none"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={RING}
          strokeDashoffset={offset}
          stroke="currentColor"
          className={scoreColor(score)}
        />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-sm font-semibold tabular-nums text-surface-900">
        {Math.round(score)}
      </span>
    </div>
  );
}

function formatDate(ms: number) {
  return new Date(ms).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function HistoryDashboard() {
  const [entries, setEntries] = useState<HistoryEntry[]>(getHistory);
  const navigate = useNavigate();

  const handleDelete = (id: string) => {
    setEntries(removeHistory(id));
  };

  const handleClear = () => {
    clearHistory();
    setEntries([]);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-surface-900">
            Past analyses
          </h1>
          <p className="mt-1 text-sm text-surface-700">
            {entries.length === 0
              ? "Your analysed resumes will appear here."
              : `${entries.length} saved ${
                  entries.length === 1 ? "analysis" : "analyses"
                } · stored on this device`}
          </p>
        </div>
        {entries.length > 0 && (
          <Button variant="secondary" onClick={handleClear}>
            Clear all
          </Button>
        )}
      </div>

      {entries.length === 0 ? (
        <Card className="flex flex-col items-center justify-center px-6 py-16 text-center">
          <span
            aria-hidden
            className="grid h-12 w-12 place-items-center rounded-full bg-brand-100 text-brand-700"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-6 w-6"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6" />
              <path d="M9 13h6M9 17h4" />
            </svg>
          </span>
          <h2 className="mt-4 text-base font-medium text-surface-900">
            No analyses yet
          </h2>
          <p className="mt-1 max-w-sm text-sm text-surface-700">
            Upload a resume to get a score and a breakdown. Each result is saved
            here so you can compare over time.
          </p>
          <Link to="/" className="mt-5">
            <Button>Analyze a resume</Button>
          </Link>
        </Card>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {entries.map((entry) => (
            <li key={entry.id}>
              <Card className="flex h-full flex-col gap-4 p-5">
                <div className="flex items-start gap-4">
                  <MiniRing score={entry.totalScore} />
                  <div className="min-w-0 flex-1">
                    <div
                      className="truncate text-sm font-medium text-surface-900"
                      title={entry.fileName}
                    >
                      {entry.fileName}
                    </div>
                    <div className="mt-0.5 text-xs text-surface-700">
                      {formatDate(entry.createdAt)}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5 text-xs text-surface-700">
                      <span className="rounded-full bg-surface-100 px-2 py-0.5 ring-1 ring-surface-200">
                        {entry.data.analysis.skills.technical.length} skills
                      </span>
                      <span className="rounded-full bg-surface-100 px-2 py-0.5 ring-1 ring-surface-200">
                        {entry.hasJobDescription
                          ? `${entry.data.score.match_score}% match`
                          : "No job desc."}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-auto flex items-center justify-between gap-2">
                  <Button
                    size="md"
                    className="flex-1"
                    onClick={() =>
                      navigate("/results", { state: entry.data })
                    }
                  >
                    View
                  </Button>
                  <button
                    type="button"
                    onClick={() => handleDelete(entry.id)}
                    aria-label={`Delete analysis of ${entry.fileName}`}
                    className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-surface-700 ring-1 ring-surface-200 transition-colors hover:bg-danger-100 hover:text-danger-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-danger-500"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4"
                    >
                      <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                      <path d="M10 11v6M14 11v6" />
                    </svg>
                  </button>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
