import Card from "./ui/Card";
import Badge from "./ui/Badge";

interface Props {
  technical: string[];
  soft: string[];
}

function Section({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "brand" | "success";
}) {
  return (
    <div>
      <h3 className="text-xs font-medium uppercase tracking-wide text-surface-700">
        {title}
      </h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.length > 0 ? (
          items.map((s) => (
            <Badge key={s} tone={tone}>
              {s}
            </Badge>
          ))
        ) : (
          <span className="text-sm text-surface-700/70">None detected</span>
        )}
      </div>
    </div>
  );
}

export default function SkillsBadges({ technical, soft }: Props) {
  return (
    <Card>
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Skills detected
      </h2>
      <div className="mt-4 space-y-4">
        <Section title="Technical" items={technical} tone="brand" />
        <Section title="Soft" items={soft} tone="success" />
      </div>
    </Card>
  );
}
