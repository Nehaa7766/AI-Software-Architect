import { cn } from "@/lib/utils";
import type { ProjectStatus } from "@/features/projects/api/projects.api";

const STYLES: Record<ProjectStatus, { badge: string; dot: string }> = {
  EXTRACTED: {
    badge:
      "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-400/20",
    dot: "bg-emerald-500",
  },
  UPLOADED: {
    badge:
      "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-400/20",
    dot: "bg-amber-500",
  },
  FAILED: {
    badge:
      "bg-rose-50 text-rose-700 ring-rose-600/20 dark:bg-rose-500/10 dark:text-rose-400 dark:ring-rose-400/20",
    dot: "bg-rose-500",
  },
};

const LABELS: Record<ProjectStatus, string> = {
  EXTRACTED: "Extracted",
  UPLOADED: "Uploaded",
  FAILED: "Failed",
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  const style = STYLES[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        style.badge,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", style.dot)} />
      {LABELS[status]}
    </span>
  );
}
