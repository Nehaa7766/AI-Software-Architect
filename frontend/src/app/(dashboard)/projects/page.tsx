"use client";

import { useCallback, useEffect, useState } from "react";
import { Github, Loader2, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/axios";
import { projectsApi, type Project } from "@/features/projects/api/projects.api";
import { ImportProjectCard } from "@/features/projects/components/ImportProjectCard";
import { StatusBadge } from "@/features/projects/components/StatusBadge";
import { StackBadges } from "@/features/projects/components/StackBadges";
import { ProjectDetailPanel } from "@/features/projects/components/ProjectDetailPanel";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

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

  const handleImported = (project: Project) => {
    setProjects((prev) => [project, ...prev]);
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await projectsApi.remove(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      toast.success("Project deleted.");
    } catch (err) {
      toast.error(getErrorMessage(err, "Delete failed."));
    } finally {
      setDeleting(null);
    }
  };

  const handleUpdated = (updated: Project) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p)),
    );
  };

  const handleDeletedFromPanel = (id: string) => {
    setProjects((prev) => prev.filter((p) => p.id !== id));
    setSelectedId(null);
  };

  const selected = projects.find((p) => p.id === selectedId) ?? null;

  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <div>
        <h1 className="mb-4 text-2xl font-bold">Projects</h1>
        <ImportProjectCard onImported={handleImported} />
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold lg:mt-12">Imported projects</h2>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : projects.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">No projects yet</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Import a ZIP or a GitHub repository to get started.
            </CardContent>
          </Card>
        ) : (
          <ul className="space-y-3">
            {projects.map((p) => (
              <li key={p.id}>
                <Card
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelectedId(p.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedId(p.id);
                    }
                  }}
                  className="cursor-pointer transition-colors hover:border-primary/50 hover:bg-secondary/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <CardContent className="flex items-center justify-between gap-4 py-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {p.source_type === "GITHUB" ? (
                          <Github className="h-4 w-4 shrink-0 text-muted-foreground" />
                        ) : (
                          <Upload className="h-4 w-4 shrink-0 text-muted-foreground" />
                        )}
                        <span className="truncate font-medium">
                          {p.project_name}
                        </span>
                        <StatusBadge status={p.status} />
                      </div>
                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {p.source_location}
                      </p>
                      {p.status === "EXTRACTED" && <StackBadges stack={p.stack} />}
                      {p.status === "FAILED" && p.error_message && (
                        <p className="mt-1 text-xs text-red-600">
                          {p.error_message}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={deleting === p.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(p.id);
                      }}
                    >
                      {deleting === p.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </div>

      {selected && (
        <ProjectDetailPanel
          project={selected}
          onClose={() => setSelectedId(null)}
          onUpdated={handleUpdated}
          onDeleted={handleDeletedFromPanel}
        />
      )}
    </div>
  );
}
