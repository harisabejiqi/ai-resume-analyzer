import Card from "./ui/Card";
import type { Grammar } from "../types";

interface Props {
  grammar?: Grammar;
}

function Header({ count }: { count?: number }) {
  return (
    <div className="flex items-center gap-2">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-4 w-4 text-brand-600"
        aria-hidden
      >
        <path d="M4 7V4h16v3M9 20h6M12 4v16" />
      </svg>
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Grammar &amp; spelling
      </h2>
      {count ? (
        <span className="ml-auto rounded-full bg-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700">
          {count} issue{count === 1 ? "" : "s"}
        </span>
      ) : null}
    </div>
  );
}

export default function GrammarCheck({ grammar }: Props) {
  if (!grammar || !grammar.available) {
    return (
      <Card>
        <Header />
        <p className="mt-4 text-sm text-surface-700/70">
          Grammar check wasn't available for this analysis.
        </p>
      </Card>
    );
  }

  if (grammar.issue_count === 0) {
    return (
      <Card>
        <Header />
        <p className="mt-4 text-sm text-surface-900">
          No grammar or spelling issues detected.
        </p>
      </Card>
    );
  }

  return (
    <Card accent="warning">
      <Header count={grammar.issue_count} />
      <ul className="mt-4 space-y-3">
        {grammar.issues.map((it, i) => (
          <li key={i} className="text-sm text-surface-900">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-surface-50 px-1.5 py-0.5 font-mono text-xs text-surface-900 line-through">
                {it.text || "—"}
              </span>
              {it.suggestions.length > 0 && (
                <>
                  <span className="text-surface-700/70" aria-hidden>
                    →
                  </span>
                  <span className="font-medium text-brand-700">
                    {it.suggestions[0]}
                  </span>
                </>
              )}
              <span className="rounded-full bg-surface-50 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-surface-700">
                {it.type}
              </span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-surface-700">
              {it.message}
            </p>
          </li>
        ))}
      </ul>
    </Card>
  );
}
