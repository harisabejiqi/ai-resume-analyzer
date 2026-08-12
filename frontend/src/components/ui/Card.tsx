import type { ReactNode } from "react";
import clsx from "clsx";

interface Props {
  children: ReactNode;
  className?: string;
  accent?: "default" | "info" | "warning";
}

const accentRing: Record<NonNullable<Props["accent"]>, string> = {
  default: "ring-surface-200/80",
  info: "ring-brand-200",
  warning: "ring-warning-500/30",
};

export default function Card({ children, className, accent = "default" }: Props) {
  return (
    <div
      className={clsx(
        "rounded-xl bg-surface-0 p-5 ring-1 shadow-sm shadow-surface-900/[0.03]",
        accentRing[accent],
        className,
      )}
    >
      {children}
    </div>
  );
}
