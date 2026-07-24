"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Loader2,
  SearchCheck,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/axios";
import { projectsApi, type Project } from "@/features/projects/api/projects.api";
import { languageColor } from "@/features/projects/lib/language-colors";
import { StatusBadge } from "@/features/projects/components/StatusBadge";

const UPCOMING = [
  "Code quality & maintainability",
  "Security vulnerabilities",
  "Performance hotspots",
  "Dead code & duplication",
];

export default function CodeReviewPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await projectsApi.list();
      setProjects(data.projects);
    } catch (err) {
      toast.error(getErrorMessage(err, "Could not load projects."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <div className="mb-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-accent">
          Analysis
        </p>
        <h1 className="mt-1.5 flex items-center gap-2 text-3xl font-bold tracking-tight text-foreground">
          <SearchCheck className="h-7 w-7 text-accent" />
          Code Review
        </h1>
        <p className="mt-1.5 max-w-prose text-sm text-muted-foreground">
          Pick a project to review — explore its structure, search symbols, and
          read source in the code viewer.
        </p>
      </div>

      {/* Upcoming automated review banner */}
      <div className="mb-6 flex flex-col gap-3 rounded-2xl border bg-card p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-accent/10 text-accent">
            <Sparkles className="h-5 w-5" />
          </span>
          <div>
            <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
              Automated review
              <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                Coming soon
              </span>
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              One-click findings for quality, security &amp; performance are on
              the way.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {UPCOMING.map((u) => (
            <span
              key={u}
              className="inline-flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-[11px] font-medium text-secondary-foreground"
            >
              <ShieldCheck className="h-3 w-3 text-accent" />
              {u}
            </span>
          ))}
        </div>
      </div>

      {/* Project picker */}
      <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        Select a project
      </h2>

      {loading ? (
        <div className="flex items-center justify-center rounded-2xl border border-dashed py-16">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed bg-card/50 px-6 py-14 text-center">
          <p className="text-sm font-medium text-foreground">No projects yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Import a codebase first, then come back to review it.
          </p>
          <Button asChild className="mt-4">
            <Link href="/projects">Go to Projects</Link>
          </Button>
        </div>
      ) : (
        <ul className="space-y-3">
          {projects.map((p) => {
            const rail = languageColor(p.primary_language);
            const disabled = p.status !== "EXTRACTED";
            return (
              <li key={p.id}>
                <Link
                  href={`/projects/${p.id}`}
                  className="group relative flex items-center gap-4 overflow-hidden rounded-xl border bg-card p-4 pl-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-elevated"
                >
                  <span
                    className="absolute inset-y-0 left-0 w-1"
                    style={{ backgroundColor: rail }}
                    aria-hidden
                  />
                  <span
                    className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-xs font-bold text-white"
                    style={{ backgroundColor: rail }}
                  >
                    {p.project_name
                      .replace(/[^a-zA-Z0-9]/g, "")
                      .slice(0, 2)
                      .toUpperCase() || "PR"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="truncate font-medium text-foreground">
                        {p.project_name}
                      </span>
                      <StatusBadge status={p.status} />
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {p.primary_language ?? "Unknown"} ·{" "}
                      <span className="font-mono tabular-nums">
                        {p.stack?.total_files ?? 0}
                      </span>{" "}
                      files
                    </p>
                  </div>
                  <span className="flex shrink-0 items-center gap-1 text-sm font-medium text-accent">
                    {disabled ? "View" : "Review"}
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
