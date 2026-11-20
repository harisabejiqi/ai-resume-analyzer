import type { ReadabilityCheck } from "../types";
import Card from "./ui/Card";

interface Props {
  checks: ReadabilityCheck[];
}

export default function ReadabilityChecks({ checks }: Props) {
  const passed = checks.filter((c) => c.passed).length;
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
          Automatic readability checks
        </h2>
        <span className="rounded-full bg-brand-100 px-2.5 py-1 text-xs font-medium text-brand-700">
          {passed} of {checks.length} passed
        </span>
      </div>
      <p className="mt-1 text-xs text-surface-700/80">
        General rules of thumb for how easy your CV is to scan. This is not a commercial
        applicant tracking system (ATS).
      </p>
      <ul className="mt-4 divide-y divide-surface-200">
        {checks.map((c) => (
          <li key={c.id} className="flex items-start gap-3 py-3">
            <span
              aria-hidden
              className={
                c.passed
                  ? "mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-success-100 text-success-500"
                  : "mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-danger-100 text-danger-500"
              }
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-3 w-3"
              >
                {c.passed ? <polyline points="20 6 9 17 4 12" /> : <path d="M6 6l12 12M18 6L6 18" />}
              </svg>
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-surface-900">
                {c.label}
                <span className="sr-only">{c.passed ? " (passed)" : " (failed)"}</span>
              </p>
              <p className="mt-0.5 text-sm text-surface-700">{c.detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
