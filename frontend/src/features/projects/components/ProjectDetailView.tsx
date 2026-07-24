"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Boxes,
  Braces,
  Code2,
  FileCode2,
  Files,
  FunctionSquare,
  Github,
  LayoutList,
  Loader2,
  RefreshCw,
  ScanSearch,
  Trash2,
  Upload,
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
import { CodeViewer, type OpenFile } from "@/features/projects/components/CodeViewer";
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
    <section className="rounded-2xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
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
    <div className="rounded-xl border bg-card p-4 shadow-sm">
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
      <p className="font-mono text-2xl font-semibold tabular-nums text-foreground">
        {value}
      </p>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative flex max-w-[260px] items-center gap-1.5 px-3.5 py-2.5 text-sm font-medium transition-colors",
        active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
      )}
    >
      {icon}
      <span className="truncate">{label}</span>
      {active && (
        <span className="absolute inset-x-2.5 -bottom-px h-0.5 rounded-full bg-accent" />
      )}
    </button>
  );
}

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [tree, setTree] = useState<ProjectTree | null>(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [symbols, setSymbols] = useState<SymbolsByFile | null>(null);
  const [tab, setTab] = useState<"overview" | "code">("overview");
  const [openFile, setOpenFile] = useState<OpenFile | null>(null);

  const refresh = useCallback(async () => {
    try {
      const fresh = await projectsApi.get(projectId);
      setProject(fresh);
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
      }
    } catch (err) {
      setNotFound(true);
      toast.error(getErrorMessage(err, "Could not load project."));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleOpenFile = (file: OpenFile) => {
    setOpenFile(file);
    setTab("code");
  };

  const handleAnalyze = async () => {
    if (!project) return;
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
    if (!project) return;
    setDetecting(true);
    try {
      setProject(await projectsApi.detect(project.id));
      toast.success("Stack re-detected.");
    } catch (err) {
      toast.error(getErrorMessage(err, "Detection failed."));
    } finally {
      setDetecting(false);
    }
  };

  const handleDelete = async () => {
    if (!project) return;
    setDeleting(true);
    try {
      await projectsApi.remove(project.id);
      toast.success("Project deleted.");
      router.push("/projects");
    } catch (err) {
      toast.error(getErrorMessage(err, "Delete failed."));
      setDeleting(false);
    }
  };

  const analyzed = !!symbols && symbols.total_symbols > 0;
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

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (notFound || !project) {
    return (
      <div className="mx-auto max-w-md py-20 text-center">
        <h1 className="text-lg font-semibold text-foreground">
          Project not found
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          It may have been deleted, or you don&rsquo;t have access to it.
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link href="/projects">
            <ArrowLeft className="h-4 w-4" /> Back to projects
          </Link>
        </Button>
      </div>
    );
  }

  const stack = project.stack;
  const rail = languageColor(project.primary_language);

  return (
    <div className="mx-auto max-w-6xl">
      {/* Back link */}
      <Link
        href="/projects"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> All projects
      </Link>

      {/* Header */}
      <div className="relative mb-6 overflow-hidden rounded-2xl border bg-card p-6 shadow-sm">
        <span
          className="absolute inset-x-0 top-0 h-1"
          style={{ backgroundColor: rail }}
          aria-hidden
        />
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              {project.source_type === "GITHUB" ? (
                <Github className="h-4 w-4 shrink-0 text-muted-foreground" />
              ) : (
                <Upload className="h-4 w-4 shrink-0 text-muted-foreground" />
              )}
              <h1 className="truncate text-2xl font-semibold tracking-tight">
                {project.project_name}
              </h1>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
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
              <span className="truncate font-mono text-xs text-muted-foreground">
                {project.source_location}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {project.status === "EXTRACTED" && tree && (
              <Button
                variant={analyzed ? "outline" : "default"}
                size="sm"
                disabled={analyzing}
                onClick={handleAnalyze}
              >
                {analyzing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ScanSearch className="h-4 w-4" />
                )}
                {analyzed ? "Re-analyze" : "Analyze code"}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
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
          </div>
        </div>
      </div>

      {project.status === "FAILED" && project.error_message && (
        <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-400">
          {project.error_message}
        </div>
      )}

      {project.status === "EXTRACTED" && (
        <>
          {/* Stats */}
          <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
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

          {/* Tabs */}
          <div className="mb-5 flex items-center gap-1 border-b">
            <TabButton
              active={tab === "overview"}
              onClick={() => setTab("overview")}
              icon={<LayoutList className="h-4 w-4" />}
              label="Overview"
            />
            <TabButton
              active={tab === "code"}
              onClick={() => setTab("code")}
              icon={<Code2 className="h-4 w-4" />}
              label={openFile ? openFile.path.split("/").pop() || "Code" : "Code"}
            />
          </div>

          {tab === "code" ? (
            <div className="h-[74vh] overflow-hidden rounded-2xl border bg-card shadow-sm">
              <CodeViewer projectId={project.id} file={openFile} />
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
              <div className="space-y-6">
                <Section title="Search symbols">
                  <SymbolSearch
                    projectId={project.id}
                    analyzed={analyzed}
                    onOpen={handleOpenFile}
                  />
                </Section>

                <Section
                  title="Folder structure"
                  action={
                    <span className="text-xs text-muted-foreground">
                      {tree?.total_files ?? 0} files · {tree?.total_dirs ?? 0}{" "}
                      folders
                    </span>
                  }
                >
                  {treeLoading ? (
                    <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading files…
                    </div>
                  ) : tree ? (
                    <>
                      {!analyzed && (
                        <p className="mb-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
                          <FileCode2 className="h-3.5 w-3.5" />
                          Run analysis to show function &amp; class counts per
                          file.
                        </p>
                      )}
                      <FileTree root={tree.root} counts={symbols?.files} />
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No files available.
                    </p>
                  )}
                </Section>
              </div>

              <div className="space-y-6">
                <Section title="Detected stack">
                  {!stack || stack.languages.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No stack detected.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      <ul className="space-y-2.5">
                        {stack.languages.map((l) => (
                          <li key={l.language}>
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-medium text-foreground">
                                {l.language}
                              </span>
                              <span className="font-mono tabular-nums text-muted-foreground">
                                {l.files} · {l.percentage}%
                              </span>
                            </div>
                            <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                              <div
                                className="h-full rounded-full"
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
                              className="rounded-md bg-accent/10 px-1.5 py-0.5 text-[11px] font-medium text-accent ring-1 ring-inset ring-accent/20"
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

                <Section title="Details">
                  <dl className="space-y-2 text-xs">
                    <div className="flex justify-between gap-2">
                      <dt className="text-muted-foreground">Imported</dt>
                      <dd className="text-foreground">
                        {formatDate(project.created_at)}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-muted-foreground">Updated</dt>
                      <dd className="text-foreground">
                        {formatDate(project.updated_at)}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-muted-foreground">Source</dt>
                      <dd className="text-foreground">
                        {project.source_type === "GITHUB" ? "GitHub" : "ZIP"}
                      </dd>
                    </div>
                  </dl>
                </Section>
              </div>
            </div>
          )}
        </>
      )}

      {project.status !== "EXTRACTED" && project.status !== "FAILED" && (
        <div className="rounded-2xl border border-dashed py-16 text-center text-sm text-muted-foreground">
          This project is still being prepared. Refresh in a moment.
        </div>
      )}
    </div>
  );
}
