import type { Analysis } from "../types";
import Card from "./ui/Card";

interface Props {
  analysis: Analysis;
}

function Field({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-surface-700">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-surface-900">
        {value || <span className="text-surface-700/70">Not found</span>}
      </dd>
    </div>
  );
}

export default function ContactInfo({ analysis }: Props) {
  return (
    <Card>
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Candidate
      </h2>
      <dl className="mt-4 grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-4">
        <Field label="Name" value={analysis.name} />
        <Field label="Email" value={analysis.email} />
        <Field label="Phone" value={analysis.phone} />
        <Field
          label="Experience"
          value={
            analysis.experience_years > 0
              ? `${analysis.experience_years} years`
              : null
          }
        />
      </dl>
    </Card>
  );
}
