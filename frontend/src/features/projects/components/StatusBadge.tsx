import { cn } from "@/lib/utils";
import type { ProjectStatus } from "@/features/projects/api/projects.api";

const STYLES: Record<ProjectStatus, string> = {
  EXTRACTED: "bg-green-100 text-green-800",
  UPLOADED: "bg-amber-100 text-amber-800",
  FAILED: "bg-red-100 text-red-800",
};

const LABELS: Record<ProjectStatus, string> = {
  EXTRACTED: "Extracted",
  UPLOADED: "Uploaded",
  FAILED: "Failed",
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STYLES[status],
      )}
    >
      {LABELS[status]}
    </span>
  );
}
