import Card from "./ui/Card";
import Badge from "./ui/Badge";

interface Props {
  keywords: string[];
}

export default function MissingKeywords({ keywords }: Props) {
  if (keywords.length === 0) return null;

  return (
    <Card accent="warning">
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Missing from your resume
      </h2>
      <p className="mt-1 text-xs text-surface-700/80">
        Frequent terms from the job description that don't appear in your CV.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {keywords.slice(0, 15).map((kw) => (
          <Badge key={kw} tone="warning">
            {kw}
          </Badge>
        ))}
      </div>
    </Card>
  );
}
