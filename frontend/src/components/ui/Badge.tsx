import type { ReactNode } from "react";
import clsx from "clsx";

interface Props {
  children: ReactNode;
  tone?: "brand" | "success" | "warning" | "neutral";
}

const tones = {
  brand: "bg-brand-100 text-brand-700 ring-brand-200",
  success: "bg-success-100 text-success-500 ring-success-500/20",
  warning: "bg-warning-100 text-warning-500 ring-warning-500/30",
  neutral: "bg-surface-100 text-surface-700 ring-surface-200",
};

export default function Badge({ children, tone = "brand" }: Props) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}
