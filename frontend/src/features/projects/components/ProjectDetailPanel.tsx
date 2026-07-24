"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Boxes,
  Braces,
  FileCode2,
  Files,
  FunctionSquare,
  Github,
  Loader2,
  RefreshCw,
  ScanSearch,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getErrorMessage } from "@/lib/axios";
import {
  projectsApi,
  type Project,
  type ProjectTree,
  type SymbolsByFile,
} from "@/features/projects/api/projects.api";
import { languageColor } from "@/features/projects/lib/language-colors";
import { FileTree } from "@/features/projects/components/FileTree";
import { StatusBadge } from "@/features/projects/components/StatusBadge";
import { SymbolSearch } from "@/features/projects/components/SymbolSearch";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function Section({
  title,
  action,
  children,
}: {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2.5">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
          {title}
        </h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function Stat({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-card p-3 shadow-subtle">
      <div
        className={cn(
          "mb-1.5 flex items-center gap-1.5 text-muted-foreground",
          accent && "text-accent",
        )}
      >
        {icon}
        <span className="text-[10px] font-medium uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="font-mono text-xl font-semibold tabular-nums text-foreground">
        {value}
      </p>
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
  const [tree, setTree] = useState<ProjectTree | null>(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [symbols, setSymbols] = useState<SymbolsByFile | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Pull the freshest record (stack may have changed since the list loaded).
  const refresh = useCallback(async () => {
    try {
      const fresh = await projectsApi.get(initial.id);
      setProject(fresh);
      // Load the folder structure + per-file symbol counts once extracted.
      if (fresh.status === "EXTRACTED") {
        setTreeLoading(true);
        try {
          const [treeData, symbolData] = await Promise.all([
            projectsApi.tree(fresh.id),
            projectsApi.symbolsByFile(fresh.id).catch(() => null),
          ]);
          setTree(treeData);
          setSymbols(symbolData);
        } catch (err) {
          toast.error(getErrorMessage(err, "Could not load folder structure."));
        } finally {
          setTreeLoading(false);
        }
      } else {
        setTree(null);
        setSymbols(null);
      }
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

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const summary = await projectsApi.parse(project.id);
      setSymbols(await projectsApi.symbolsByFile(project.id));
      toast.success(
        `Analyzed ${summary.files_parsed} files · ${summary.total_symbols} symbols.`,
      );
    } catch (err) {
      toast.error(getErrorMessage(err, "Code analysis failed."));
    } finally {
      setAnalyzing(false);
    }
  };

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
  const rail = languageColor(project.primary_language);
  const analyzed = !!symbols && symbols.total_symbols > 0;

  // Aggregate symbol totals for the summary grid.
  const symbolTotals = useMemo(() => {
    if (!symbols) return { functions: 0, classes: 0, total: 0 };
    let functions = 0;
    let classes = 0;
    for (const c of Object.values(symbols.files)) {
      functions += c.functions + c.methods;
      classes += c.classes;
    }
    return { functions, classes, total: symbols.total_symbols };
  }, [symbols]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-950/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
        aria-hidden
      />
      {/* Panel */}
      <aside className="relative flex h-full w-full max-w-lg flex-col overflow-hidden border-l bg-background shadow-panel animate-panel-in">
        {/* Header */}
        <header className="relative border-b px-6 py-5">
          <span
            className="absolute inset-x-0 top-0 h-1"
            style={{ backgroundColor: rail }}
            aria-hidden
          />
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                {project.source_type === "GITHUB" ? (
                  <Github className="h-4 w-4 shrink-0 text-muted-foreground" />
                ) : (
                  <Upload className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
                <h2 className="truncate text-lg font-semibold tracking-tight">
                  {project.project_name}
                </h2>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <StatusBadge status={project.status} />
                {project.primary_language && (
                  <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: rail }}
                    />
                    {project.primary_language}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </header>

        {loading ? (
          <div className="flex flex-1 items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="scrollbar-slim flex-1 space-y-7 overflow-y-auto p-6">
            {/* Summary stats */}
            {project.status === "EXTRACTED" && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat
                  icon={<Files className="h-3.5 w-3.5" />}
                  label="Files"
                  value={tree?.total_files ?? stack?.total_files ?? 0}
                />
                <Stat
                  icon={<Boxes className="h-3.5 w-3.5" />}
                  label="Symbols"
                  value={symbolTotals.total}
                  accent={analyzed}
                />
                <Stat
                  icon={<FunctionSquare className="h-3.5 w-3.5" />}
                  label="Functions"
                  value={symbolTotals.functions}
                />
                <Stat
                  icon={<Braces className="h-3.5 w-3.5" />}
                  label="Classes"
                  value={symbolTotals.classes}
                />
              </div>
            )}

            {project.status === "FAILED" && project.error_message && (
              <Section title="Error">
                <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-400">
                  {project.error_message}
                </div>
              </Section>
            )}

            {/* Detected stack */}
            <Section title="Detected stack">
              {!stack || stack.languages.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No stack detected.
                </p>
              ) : (
                <div className="space-y-4">
                  {/* Language breakdown with share bars */}
                  <ul className="space-y-2.5">
                    {stack.languages.map((l) => (
                      <li key={l.language}>
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium text-foreground">
                            {l.language}
                          </span>
                          <span className="font-mono tabular-nums text-muted-foreground">
                            {l.files} {l.files === 1 ? "file" : "files"} ·{" "}
                            {l.percentage}%
                          </span>
                        </div>
                        <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${Math.max(l.percentage, 2)}%`,
                              backgroundColor: languageColor(l.language),
                            }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>

                  {(stack.frameworks.length > 0 ||
                    stack.package_managers.length > 0) && (
                    <div className="flex flex-wrap gap-1.5 border-t pt-3">
                      {stack.frameworks.map((f) => (
                        <span
                          key={f}
                          className="rounded-md bg-sky-50 px-1.5 py-0.5 text-[11px] font-medium text-sky-700 ring-1 ring-inset ring-sky-600/15 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-400/20"
                        >
                          {f}
                        </span>
                      ))}
                      {stack.package_managers.map((p) => (
                        <span
                          key={p}
                          className="rounded-md bg-secondary px-1.5 py-0.5 text-[11px] font-medium text-secondary-foreground ring-1 ring-inset ring-border"
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Section>

            {/* Symbol search */}
            {project.status === "EXTRACTED" && (
              <Section title="Search symbols">
                <SymbolSearch projectId={project.id} analyzed={analyzed} />
              </Section>
            )}

            {/* Folder structure */}
            {project.status === "EXTRACTED" && (
              <Section
                title="Folder structure"
                action={
                  tree && (
                    <Button
                      variant={analyzed ? "outline" : "default"}
                      size="sm"
                      className="h-7 shrink-0 px-2.5 text-xs"
                      disabled={analyzing}
                      onClick={handleAnalyze}
                      title="Parse the code to count functions and classes per file"
                    >
                      {analyzing ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <ScanSearch className="h-3.5 w-3.5" />
                      )}
                      {analyzed ? "Re-analyze" : "Analyze code"}
                    </Button>
                  )
                }
              >
                {treeLoading ? (
                  <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading files…
                  </div>
                ) : tree ? (
                  <div className="space-y-2">
                    <p className="flex flex-wrap items-center gap-x-1.5 text-xs text-muted-foreground">
                      <FileCode2 className="h-3.5 w-3.5" />
                      <span className="font-mono tabular-nums text-foreground">
                        {tree.total_files}
                      </span>
                      {tree.total_files === 1 ? "file" : "files"} ·{" "}
                      <span className="font-mono tabular-nums text-foreground">
                        {tree.total_dirs}
                      </span>
                      {tree.total_dirs === 1 ? "folder" : "folders"}
                      {analyzed && (
                        <>
                          {" · "}
                          <span className="font-mono tabular-nums text-accent">
                            {symbols?.total_symbols}
                          </span>
                          symbols
                        </>
                      )}
                      {tree.truncated && " · truncated"}
                    </p>
                    {!analyzed && (
                      <p className="text-[11px] text-muted-foreground">
                        Run analysis to show function &amp; class counts on each
                        file.
                      </p>
                    )}
                    <FileTree root={tree.root} counts={symbols?.files} />
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No files available.
                  </p>
                )}
              </Section>
            )}

            {/* Source + timeline */}
            <Section title="Source">
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-xs text-muted-foreground">Location</dt>
                  <dd className="break-all font-mono text-xs text-foreground">
                    {project.source_location}
                  </dd>
                </div>
                <div className="grid grid-cols-2 gap-2 border-t pt-2 text-xs">
                  <div>
                    <dt className="text-muted-foreground">Imported</dt>
                    <dd className="text-foreground">
                      {formatDate(project.created_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Updated</dt>
                    <dd className="text-foreground">
                      {formatDate(project.updated_at)}
                    </dd>
                  </div>
                </div>
              </dl>
            </Section>
          </div>
        )}

        {/* Footer actions */}
        <footer className="flex items-center gap-2 border-t bg-card/50 p-4">
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
            Re-detect stack
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:hover:bg-rose-500/10"
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
