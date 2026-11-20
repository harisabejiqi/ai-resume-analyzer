import type { CvQuality } from "../types";
import Card from "./ui/Card";

interface Props {
  summary: CvQuality["summary"];
  statistics: CvQuality["statistics"];
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-surface-50 px-4 py-3 ring-1 ring-surface-200/80">
      <div className="font-display text-xl font-semibold tabular-nums text-surface-900">{value}</div>
      <div className="mt-0.5 text-xs text-surface-700">{label}</div>
    </div>
  );
}

export default function CvSummary({ summary, statistics: s }: Props) {
  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">Summary</h2>
        <p className="mt-1 text-xs text-surface-700/80">
          {summary.method === "sbert_centroid"
            ? "The lines most representative of your CV, copied word for word in their original order."
            : "The first lines of your CV, copied word for word."}
        </p>
        {summary.sentences.length ? (
          <ul className="mt-4 space-y-2.5">
            {summary.sentences.map((line, i) => (
              <li
                key={i}
                className="border-l-2 border-brand-200 pl-3 text-sm leading-relaxed text-surface-900"
              >
                {line}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-sm text-surface-700/70">Not enough text to summarise.</p>
        )}
      </Card>

      <Card>
        <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">Statistics</h2>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <Stat label="Words" value={s.word_count} />
          <Stat label="Sections found" value={s.sections.length} />
          <Stat label="Roles" value={s.roles} />
          <Stat label="Experience bullets" value={s.bullet_count} />
          <Stat label="Bullets per role" value={s.avg_bullets_per_role} />
          <Stat label="Words per bullet" value={s.avg_words_per_bullet} />
          <Stat label="Bullets with a number" value={`${Math.round(s.quantified_bullets_pct)}%`} />
          <Stat label="Bullets with an action verb" value={`${Math.round(s.action_verb_bullets_pct)}%`} />
          <Stat label="Technical skills" value={s.technical_skills} />
          <Stat label="Soft skills" value={s.soft_skills} />
          <Stat label="Education entries" value={s.education_entries} />
          <Stat label="Years of experience" value={s.experience_years} />
        </div>
      </Card>
    </div>
  );
}
