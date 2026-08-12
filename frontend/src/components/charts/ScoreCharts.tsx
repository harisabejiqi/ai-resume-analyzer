import type { Score } from "../../types";
import Card from "../ui/Card";
import RadarChart, { type RadarDatum } from "./RadarChart";
import CompositionDonut, { type DonutSegment } from "./CompositionDonut";

interface Props {
  score: Score;
}

const LABELS: Record<string, string> = {
  skills: "Skills",
  education: "Education",
  experience: "Experience",
  relevance: "Relevance",
};

const COLORS: Record<string, string> = {
  skills: "var(--color-brand-500)",
  education: "var(--color-success-500)",
  experience: "var(--color-warning-500)",
  relevance: "var(--color-brand-300)",
};

const WEIGHTS_WITH_JD: Record<string, number> = {
  skills: 0.3,
  education: 0.2,
  experience: 0.2,
  relevance: 0.3,
};
const WEIGHTS_NO_JD: Record<string, number> = {
  skills: 30 / 70,
  education: 20 / 70,
  experience: 20 / 70,
};

export default function ScoreCharts({ score }: Props) {
  const entries = Object.entries(score.breakdown) as [string, number][];
  const weights = score.has_job_description ? WEIGHTS_WITH_JD : WEIGHTS_NO_JD;

  const radarData: RadarDatum[] = entries.map(([key, value]) => ({
    label: LABELS[key] ?? key,
    value,
  }));

  const segments: DonutSegment[] = entries.map(([key, value]) => ({
    label: LABELS[key] ?? key,
    value: value * (weights[key] ?? 0),
    color: COLORS[key] ?? "var(--color-surface-300)",
  }));

  return (
    <Card>
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Visual breakdown
      </h2>
      <div className="mt-5 grid gap-8 md:grid-cols-2">
        <figure className="flex flex-col items-center">
          <RadarChart data={radarData} />
          <figcaption className="mt-2 text-center text-xs text-surface-700">
            Category scores (0–100)
          </figcaption>
        </figure>
        <figure className="flex flex-col justify-center">
          <CompositionDonut
            segments={segments}
            centerValue={score.total_score}
            centerLabel="score"
          />
          <figcaption className="mt-3 text-center text-xs text-surface-700">
            Each category's contribution to the total
          </figcaption>
        </figure>
      </div>
    </Card>
  );
}
