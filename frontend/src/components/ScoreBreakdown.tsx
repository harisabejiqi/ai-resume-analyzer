import type { AnalyzeResponse, CvPart } from "../types";

interface Props {
  data: AnalyzeResponse;
}

const TITLES: Record<CvPart, string> = {
  experience: "Experience content",
  skills: "Skills",
  contact: "Contact details",
  language: "Language",
  education: "Education",
  length: "Length",
};

interface Category {
  key: string;
  title: string;
  value: number;
  weight: number;
  notes: string[];
}

function tone(value: number) {
  if (value >= 70) return { bar: "bg-success-500", text: "text-success-500", kind: "ok" as const };
  if (value >= 40) return { bar: "bg-warning-500", text: "text-warning-500", kind: "warn" as const };
  return { bar: "bg-danger-500", text: "text-danger-500", kind: "bad" as const };
}

function StatusIcon({ kind, className }: { kind: "ok" | "warn" | "bad"; className: string }) {
  return (
    <svg viewBox="0 0 24 24" className={`h-5 w-5 shrink-0 ${className}`} aria-hidden>
      <circle cx="12" cy="12" r="11" fill="currentColor" />
      <g fill="none" stroke="white" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        {kind === "ok" && <polyline points="7 12.5 10.5 16 17 9" />}
        {kind === "warn" && <path d="M12 7v6M12 17h.01" />}
        {kind === "bad" && <path d="M8.5 8.5l7 7M15.5 8.5l-7 7" />}
      </g>
    </svg>
  );
}

function notesFor(part: CvPart, { analysis, grammar, cv_quality }: AnalyzeResponse): string[] {
  const stats = cv_quality.statistics;
  const { technical, soft } = analysis.skills;
  switch (part) {
    case "experience":
      return stats.roles
        ? [
            `${stats.bullet_count} bullet${stats.bullet_count === 1 ? "" : "s"} across ${stats.roles} role${stats.roles === 1 ? "" : "s"}.`,
            `${Math.round(stats.quantified_bullets_pct)}% include a measurable result; ${Math.round(stats.action_verb_bullets_pct)}% start with an action verb.`,
          ]
        : ["No work experience could be parsed."];
    case "skills":
      return [
        `${technical.length} technical and ${soft.length} soft skills detected.`,
        ...(technical.length
          ? [`Includes ${technical.slice(0, 6).join(", ")}${technical.length > 6 ? ` and ${technical.length - 6} more` : ""}.`]
          : ["List your technical skills in a dedicated Skills section."]),
      ];
    case "contact":
      return [
        analysis.email ? "Email found." : "No email address found.",
        analysis.phone ? "Phone number found." : "No phone number found.",
      ];
    case "language":
      return [
        grammar.issue_count
          ? `${grammar.issue_count} grammar or spelling issue${grammar.issue_count === 1 ? "" : "s"} found.`
          : "No grammar or spelling issues found.",
      ];
    case "education":
      return analysis.education.length
        ? analysis.education.slice(0, 2)
        : ["No education entries detected."];
    case "length":
      return [`${stats.word_count} words (recommended 150 to 1000).`];
  }
}

function buildCategories(data: AnalyzeResponse): Category[] {
  return (Object.keys(TITLES) as CvPart[]).flatMap((part) => {
    const entry = data.cv_quality.breakdown[part];
    if (!entry) return [];
    return [{
      key: part,
      title: TITLES[part],
      value: entry.score,
      weight: Math.round(entry.weight * 100),
      notes: notesFor(part, data),
    }];
  });
}

export default function ScoreBreakdown({ data }: Props) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {buildCategories(data).map((c) => {
        const t = tone(c.value);
        const value = Math.max(0, Math.min(100, c.value));
        return (
          <article
            key={c.key}
            className="rounded-xl bg-surface-50 p-5 ring-1 ring-surface-200/80"
          >
            <div className="flex items-center gap-3">
              <StatusIcon kind={t.kind} className={t.text} />
              <h3 className="font-medium text-surface-900">{c.title}</h3>
              <span className="ml-auto text-sm font-semibold tabular-nums text-brand-600">
                {Math.round(value)}/100
              </span>
            </div>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-surface-200">
              <div
                className={`h-full rounded-full transition-[width] duration-700 ease-out ${t.bar}`}
                style={{ width: `${value}%` }}
              />
            </div>
            <ul className="mt-4 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-surface-700 marker:text-surface-300">
              {c.notes.map((n, i) => (
                <li key={i}>{n}</li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-surface-700/70">
              {c.weight}% of the CV quality score
            </p>
          </article>
        );
      })}
    </div>
  );
}
