import Card from "./ui/Card";

interface Props {
  education: string[];
}

export default function EducationList({ education }: Props) {
  return (
    <Card>
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Education
      </h2>
      {education.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {education.map((edu, i) => (
            <li
              key={i}
              className="flex items-start gap-3 rounded-md bg-surface-50 px-3 py-2 text-sm text-surface-900"
            >
              <span
                aria-hidden
                className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500"
              />
              <span>{edu}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-surface-700/70">
          No education details detected.
        </p>
      )}
    </Card>
  );
}
