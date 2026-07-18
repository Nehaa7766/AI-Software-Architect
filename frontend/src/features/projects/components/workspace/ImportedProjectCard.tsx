"use client";

import { Github, Loader2, MoreVertical, Trash2, Upload } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Project } from "@/features/projects/api/projects.api";
import { languageColor } from "@/features/projects/lib/language-colors";
import { StatusBadge } from "@/features/projects/components/StatusBadge";

function formatBytes(bytes: number): string {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const mins = Math.max(1, Math.round((Date.now() - then) / 60000));
  if (mins < 60) return `${mins} min${mins === 1 ? "" : "s"} ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export function ImportedProjectCard({
  project: p,
  deleting,
  onOpen,
  onDelete,
}: {
  project: Project;
  deleting: boolean;
  onOpen: () => void;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const stack = p.stack;
  const initials = p.project_name.replace(/[^a-zA-Z0-9]/g, "").slice(0, 3).toUpperCase() || "PRJ";
  const rail = languageColor(p.primary_language);

  return (
    <div className="rounded-2xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-elevated">
      {/* Header row */}
      <div className="flex items-start gap-3">
        <span
          className="grid h-11 w-11 shrink-0 place-items-center rounded-xl text-sm font-bold text-white"
          style={{ backgroundColor: rail }}
        >
          {initials}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {p.source_type === "GITHUB" ? (
              <Github className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            ) : (
              <Upload className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            )}
            <span className="truncate font-semibold text-foreground">
              {p.project_name}
            </span>
            <StatusBadge status={p.status} />
          </div>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
            {stack && stack.total_source_bytes > 0 && (
              <span className="font-mono tabular-nums">
                {formatBytes(stack.total_source_bytes)}
              </span>
            )}
            <span aria-hidden>·</span>
            <span>{timeAgo(p.created_at)}</span>
          </p>
        </div>

        {/* Menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            onBlur={() => setTimeout(() => setMenuOpen(false), 120)}
            className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            aria-label="Project actions"
          >
            {deleting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <MoreVertical className="h-4 w-4" />
            )}
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-9 z-10 w-36 overflow-hidden rounded-lg border bg-card py-1 shadow-elevated">
              <button
                onClick={onOpen}
                className="block w-full px-3 py-1.5 text-left text-sm hover:bg-secondary"
              >
                Open project
              </button>
              <button
                onClick={onDelete}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-500/10"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {p.status === "FAILED" && p.error_message && (
        <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-400">
          {p.error_message}
        </p>
      )}

      {p.status === "EXTRACTED" && stack && stack.languages.length > 0 && (
        <>
          {/* Technology breakdown */}
          <div className="mt-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Technology Breakdown
            </p>
            {/* Combined bar */}
            <div className="flex h-2 w-full overflow-hidden rounded-full bg-secondary">
              {stack.languages.slice(0, 6).map((l) => (
                <div
                  key={l.language}
                  style={{
                    width: `${l.percentage}%`,
                    backgroundColor: languageColor(l.language),
                  }}
                  title={`${l.language} ${l.percentage}%`}
                />
              ))}
            </div>
            {/* Legend */}
            <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5">
              {stack.languages.slice(0, 4).map((l) => (
                <span
                  key={l.language}
                  className="flex items-center gap-1.5 text-xs"
                >
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: languageColor(l.language) }}
                  />
                  <span className="text-foreground">{l.language}</span>
                  <span className="font-mono tabular-nums text-muted-foreground">
                    {l.percentage}%
                  </span>
                </span>
              ))}
            </div>
          </div>

          {/* Stack detected */}
          {(stack.frameworks.length > 0 ||
            stack.package_managers.length > 0) && (
            <div className="mt-4">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Stack Detected
              </p>
              <div className="flex flex-wrap gap-1.5">
                {stack.frameworks.map((f) => (
                  <span
                    key={f}
                    className="rounded-md bg-accent/10 px-2 py-0.5 text-[11px] font-medium text-accent ring-1 ring-inset ring-accent/20"
                  >
                    {f}
                  </span>
                ))}
                {stack.package_managers.map((pm) => (
                  <span
                    key={pm}
                    className="rounded-md bg-secondary px-2 py-0.5 text-[11px] font-medium text-secondary-foreground ring-1 ring-inset ring-border"
                  >
                    {pm}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <Button
        onClick={onOpen}
        className={cn("mt-5 w-full")}
        disabled={p.status !== "EXTRACTED"}
      >
        Open Project
      </Button>
    </div>
  );
}
