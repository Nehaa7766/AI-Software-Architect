import { FileArchive, GitBranch, Radar, ScanLine } from "lucide-react";

import type { Project } from "@/features/projects/api/projects.api";

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const secs = Math.max(1, Math.round((Date.now() - then) / 1000));
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

type Item = {
  icon: typeof FileArchive;
  title: string;
  time: string;
};

/**
 * Recent Activity. Seeds from the most recent imported project (real data) and
 * appends the analysis steps that follow an import.
 */
export function RecentActivity({ projects }: { projects: Project[] }) {
  const latest = [...projects].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )[0];

  const items: Item[] = latest
    ? [
        {
          icon: latest.source_type === "GITHUB" ? GitBranch : FileArchive,
          title: `${
            latest.source_type === "GITHUB" ? "Repository" : "ZIP"
          } imported · ${latest.project_name}`,
          time: timeAgo(latest.created_at),
        },
        {
          icon: ScanLine,
          title: `Stack detected · ${latest.primary_language ?? "analyzing"}`,
          time: timeAgo(latest.updated_at),
        },
        {
          icon: Radar,
          title: "Dependencies mapped",
          time: timeAgo(latest.updated_at),
        },
      ]
    : [
        { icon: FileArchive, title: "No activity yet", time: "" },
      ];

  return (
    <div className="rounded-2xl bg-forest p-5 text-forest-foreground shadow-elevated">
      <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-forest-foreground/70">
        Recent Activity
      </h3>
      <ul className="space-y-3.5">
        {items.map((item, i) => {
          const Icon = item.icon;
          return (
            <li key={i} className="flex items-start gap-3">
              <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-bright/15 text-brand-bright">
                <Icon className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-white">
                  {item.title}
                </p>
                {item.time && (
                  <p className="text-[10px] text-forest-foreground/50">
                    {item.time}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      <button className="mt-4 w-full rounded-lg border border-white/10 py-2 text-xs font-medium text-forest-foreground/80 transition-colors hover:bg-forest-700 hover:text-white">
        View all activity
      </button>
    </div>
  );
}
