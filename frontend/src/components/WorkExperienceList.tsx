import Card from "./ui/Card";
import type { WorkExperience } from "../types";

interface Props {
  workExperience: WorkExperience[];
}

function formatDuration(months: number): string | null {
  if (months <= 0) return null;
  const years = Math.floor(months / 12);
  const rem = months % 12;
  const parts: string[] = [];
  if (years) parts.push(`${years} yr${years > 1 ? "s" : ""}`);
  if (rem) parts.push(`${rem} mo`);
  return parts.join(" ");
}

export default function WorkExperienceList({ workExperience }: Props) {
  return (
    <Card>
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Work Experience
      </h2>
      {workExperience.length > 0 ? (
        <ul className="mt-4 space-y-4">
          {workExperience.map((entry, i) => {
            const dates = [entry.start, entry.end].filter(Boolean).join(" – ");
            const duration = formatDuration(entry.duration_months);
            return (
              <li
                key={i}
                className="rounded-md bg-surface-50 px-3 py-3 text-sm text-surface-900"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <span className="font-medium">
                    {entry.title || "Role"}
                    {entry.company && (
                      <span className="font-normal text-surface-700">
                        {" "}
                        · {entry.company}
                      </span>
                    )}
                  </span>
                  {dates && (
                    <span className="text-xs text-surface-700/80">
                      {dates}
                      {duration && ` (${duration})`}
                    </span>
                  )}
                </div>
                {entry.bullets.length > 0 && (
                  <ul className="mt-2 space-y-1.5">
                    {entry.bullets.map((bullet, j) => (
                      <li key={j} className="flex items-start gap-2 text-surface-900">
                        <span
                          aria-hidden
                          className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-500"
                        />
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-surface-700/70">
          No work experience section detected.
        </p>
      )}
    </Card>
  );
}
