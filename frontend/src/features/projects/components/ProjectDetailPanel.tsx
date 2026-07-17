"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Github,
  Loader2,
  RefreshCw,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/axios";
import { projectsApi, type Project } from "@/features/projects/api/projects.api";
import { StatusBadge } from "@/features/projects/components/StatusBadge";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      {children}
    </div>
  );
}

export function ProjectDetailPanel({
  project: initial,
  onClose,
  onUpdated,
  onDeleted,
}: {
  project: Project;
  onClose: () => void;
  onUpdated: (project: Project) => void;
  onDeleted: (id: string) => void;
}) {
  const [project, setProject] = useState<Project>(initial);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Pull the freshest record (stack may have changed since the list loaded).
  const refresh = useCallback(async () => {
    try {
      const fresh = await projectsApi.get(initial.id);
      setProject(fresh);
    } catch (err) {
      toast.error(getErrorMessage(err, "Could not load project."));
    } finally {
      setLoading(false);
    }
  }, [initial.id]);

  useEffect(() => {
    setProject(initial);
    setLoading(true);
    refresh();
  }, [initial, refresh]);

  // Close on Escape.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleDetect = async () => {
    setDetecting(true);
    try {
      const updated = await projectsApi.detect(project.id);
      setProject(updated);
      onUpdated(updated);
      toast.success("Stack re-detected.");
    } catch (err) {
      toast.error(getErrorMessage(err, "Detection failed."));
    } finally {
      setDetecting(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await projectsApi.remove(project.id);
      onDeleted(project.id);
      toast.success("Project deleted.");
      onClose();
    } catch (err) {
      toast.error(getErrorMessage(err, "Delete failed."));
      setDeleting(false);
    }
  };

  const stack = project.stack;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-hidden
      />
      {/* Panel */}
      <aside className="relative flex h-full w-full max-w-md flex-col overflow-y-auto border-l bg-background shadow-xl">
        <header className="flex items-start justify-between gap-3 border-b p-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              {project.source_type === "GITHUB" ? (
                <Github className="h-4 w-4 shrink-0 text-muted-foreground" />
              ) : (
                <Upload className="h-4 w-4 shrink-0 text-muted-foreground" />
              )}
              <h2 className="truncate text-lg font-semibold">
                {project.project_name}
              </h2>
            </div>
            <div className="mt-1">
              <StatusBadge status={project.status} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-secondary"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {loading ? (
          <div className="flex flex-1 items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="flex-1 space-y-6 p-5">
            <Section title="Source">
              <p className="break-all text-sm">{project.source_location}</p>
              <p className="text-xs text-muted-foreground">
                {project.source_type === "GITHUB"
                  ? "GitHub repository"
                  : "Uploaded ZIP"}
              </p>
            </Section>

            {project.status === "FAILED" && project.error_message && (
              <Section title="Error">
                <p className="text-sm text-red-600">{project.error_message}</p>
              </Section>
            )}

            <Section title="Detected stack">
              {!stack || stack.languages.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No stack detected.
                </p>
              ) : (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                    <span>
                      Primary:{" "}
                      <span className="font-medium text-foreground">
                        {stack.primary_language ?? "—"}
                      </span>
                    </span>
                    <span>{stack.total_files} source files</span>
                  </div>

                  {/* Language breakdown with share bars */}
                  <ul className="space-y-2">
                    {stack.languages.map((l) => (
                      <li key={l.language}>
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium">{l.language}</span>
                          <span className="text-muted-foreground">
                            {l.files} {l.files === 1 ? "file" : "files"} ·{" "}
                            {l.percentage}%
                          </span>
                        </div>
                        <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                          <div
                            className="h-full bg-indigo-500"
                            style={{ width: `${Math.max(l.percentage, 2)}%` }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>

                  {stack.frameworks.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs text-muted-foreground">
                        Frameworks
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {stack.frameworks.map((f) => (
                          <span
                            key={f}
                            className="rounded bg-sky-100 px-1.5 py-0.5 text-[11px] font-medium text-sky-800"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {stack.package_managers.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs text-muted-foreground">
                        Package managers
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {stack.package_managers.map((p) => (
                          <span
                            key={p}
                            className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-700"
                          >
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Section>

            <Section title="Timeline">
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs">
                <dt className="text-muted-foreground">Imported</dt>
                <dd>{formatDate(project.created_at)}</dd>
                <dt className="text-muted-foreground">Updated</dt>
                <dd>{formatDate(project.updated_at)}</dd>
              </dl>
            </Section>
          </div>
        )}

        <footer className="flex items-center gap-2 border-t p-4">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            disabled={detecting || project.status !== "EXTRACTED"}
            onClick={handleDetect}
          >
            {detecting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Re-detect
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={deleting}
            onClick={handleDelete}
          >
            {deleting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            Delete
          </Button>
        </footer>
      </aside>
    </div>
  );
}
