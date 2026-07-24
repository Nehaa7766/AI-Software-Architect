"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Layers, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { getErrorMessage } from "@/lib/axios";
import { projectsApi, type Project } from "@/features/projects/api/projects.api";
import { ImportProjectCard } from "@/features/projects/components/ImportProjectCard";
import { AgentSwarm } from "@/features/projects/components/workspace/AgentSwarm";
import { ArchitectureHealth } from "@/features/projects/components/workspace/ArchitectureHealth";
import { ImportedProjectCard } from "@/features/projects/components/workspace/ImportedProjectCard";
import { RecentActivity } from "@/features/projects/components/workspace/RecentActivity";
import { WorkspaceHero } from "@/features/projects/components/workspace/WorkspaceHero";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

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

  const handleImported = (project: Project) =>
    setProjects((prev) => [project, ...prev]);

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

  return (
    <div className="mx-auto max-w-[1400px]">
      <WorkspaceHero />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.1fr)_340px]">
        {/* Import column */}
        <div className="xl:sticky xl:top-24 xl:self-start">
          <ImportProjectCard onImported={handleImported} />
        </div>

        {/* Imported projects column */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Imported Projects
            </h2>
            {!loading && (
              <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium tabular-nums text-muted-foreground">
                {projects.length} {projects.length === 1 ? "Project" : "Projects"}
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center rounded-2xl border border-dashed py-20">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : projects.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-4">
              {projects.map((p) => (
                <ImportedProjectCard
                  key={p.id}
                  project={p}
                  deleting={deleting === p.id}
                  onOpen={() => router.push(`/projects/${p.id}`)}
                  onDelete={() => handleDelete(p.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right rail */}
        <div className="space-y-6">
          <ArchitectureHealth />
          <RecentActivity projects={projects} />
        </div>
      </div>

      <AgentSwarm />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed bg-card/50 px-6 py-16 text-center">
      <span className="mb-4 grid h-12 w-12 place-items-center rounded-xl bg-accent/10 text-accent">
        <Layers className="h-6 w-6" />
      </span>
      <h3 className="text-sm font-semibold text-foreground">No projects yet</h3>
      <p className="mt-1 max-w-xs text-sm text-muted-foreground">
        Import a ZIP archive or a public GitHub repository to start exploring a
        codebase.
      </p>
    </div>
  );
}
