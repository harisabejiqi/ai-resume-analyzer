import Card from "./ui/Card";

interface Props {
  suggestions: string[];
}

export default function Suggestions({ suggestions }: Props) {
  return (
    <Card accent="info">
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
          <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.6 1 1.5 1 2.3v1h6v-1c0-.8.4-1.7 1-2.3A7 7 0 0 0 12 2z" />
        </svg>
        <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
          Improvement suggestions
        </h2>
      </div>
      <ul className="mt-4 space-y-2.5">
        {suggestions.map((s, i) => (
          <li key={i} className="flex items-start gap-3 text-sm text-surface-900">
            <span
              aria-hidden
              className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-brand-100 text-[10px] font-semibold text-brand-700"
            >
              {i + 1}
            </span>
            <span className="leading-relaxed">{s}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
