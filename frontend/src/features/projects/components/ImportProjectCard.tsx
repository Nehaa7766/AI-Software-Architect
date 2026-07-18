"use client";

import { useState } from "react";
import { Github, Loader2, ShieldCheck, UploadCloud } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getErrorMessage } from "@/lib/axios";
import { projectsApi, type Project } from "@/features/projects/api/projects.api";

type Method = "zip" | "github";

export function ImportProjectCard({
  onImported,
}: {
  onImported: (project: Project) => void;
}) {
  const [method, setMethod] = useState<Method>("zip");
  const [file, setFile] = useState<File | null>(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);

  const reset = () => {
    setFile(null);
    setRepoUrl("");
    setProgress(null);
  };

  const pickFile = (f: File | null) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".zip")) {
      toast.error("Only .zip archives are accepted.");
      return;
    }
    setFile(f);
  };

  const handleZip = async () => {
    if (!file) {
      toast.error("Choose a .zip file first.");
      return;
    }
    setSubmitting(true);
    setProgress(0);
    try {
      const project = await projectsApi.uploadZip(file, setProgress);
      toast.success(`Imported "${project.project_name}".`);
      onImported(project);
      reset();
    } catch (err) {
      toast.error(getErrorMessage(err, "Upload failed."));
    } finally {
      setSubmitting(false);
      setProgress(null);
    }
  };

  const handleGithub = async () => {
    if (!repoUrl.trim()) {
      toast.error("Enter a GitHub repository URL.");
      return;
    }
    setSubmitting(true);
    try {
      const project = await projectsApi.importGithub(repoUrl.trim());
      toast.success(`Imported "${project.project_name}".`);
      onImported(project);
      reset();
    } catch (err) {
      toast.error(getErrorMessage(err, "GitHub import failed."));
    } finally {
      setSubmitting(false);
    }
  };

  const submit = () => (method === "zip" ? handleZip() : handleGithub());

  return (
    <div className="rounded-2xl border bg-card p-5 shadow-sm">
      <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        Import New Project
      </h2>

      {/* Method tabs */}
      <div className="mt-3 inline-flex w-full rounded-xl bg-secondary p-1">
        <TabButton
          active={method === "zip"}
          onClick={() => setMethod("zip")}
          icon={<UploadCloud className="h-4 w-4" />}
          label="From ZIP"
        />
        <TabButton
          active={method === "github"}
          onClick={() => setMethod("github")}
          icon={<Github className="h-4 w-4" />}
          label="From GitHub"
        />
      </div>

      {method === "zip" ? (
        <div className="mt-4 space-y-3">
          {/* Drop zone */}
          <label
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              pickFile(e.dataTransfer.files?.[0] ?? null);
            }}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors",
              dragging
                ? "border-accent bg-accent/5"
                : "border-border hover:border-accent/50 hover:bg-secondary/50",
            )}
          >
            <span className="grid h-11 w-11 place-items-center rounded-full bg-accent/10 text-accent">
              <UploadCloud className="h-5 w-5" />
            </span>
            <span className="text-sm font-medium text-foreground">
              Drag &amp; drop ZIP file here
            </span>
            <span className="text-xs text-muted-foreground">
              or click to browse — max 100 MB
            </span>
            <input
              type="file"
              accept=".zip,application/zip"
              disabled={submitting}
              className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
            />
          </label>

          {file && (
            <div className="flex items-center justify-between rounded-lg border bg-secondary/40 px-3 py-2 text-xs">
              <span className="truncate font-mono text-foreground">
                {file.name}
              </span>
              <span className="ml-2 shrink-0 font-mono tabular-nums text-muted-foreground">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4 space-y-2">
          <label
            htmlFor="repo"
            className="text-xs font-medium text-foreground"
          >
            GitHub repository URL
          </label>
          <Input
            id="repo"
            type="url"
            placeholder="https://github.com/user/project"
            value={repoUrl}
            disabled={submitting}
            onChange={(e) => setRepoUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Public repositories only.
          </p>
        </div>
      )}

      {progress !== null && (
        <div className="mt-4 space-y-1">
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full bg-accent transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {progress < 100 ? `Uploading… ${progress}%` : "Extracting…"}
          </p>
        </div>
      )}

      <Button
        onClick={submit}
        disabled={submitting}
        className="mt-4 w-full"
        size="lg"
      >
        {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
        Import Project
      </Button>

      <p className="mt-3 flex items-start gap-1.5 text-[11px] text-muted-foreground">
        <ShieldCheck className="mt-px h-3.5 w-3.5 shrink-0 text-accent" />
        Your code is 100% private and secure. It is never run or executed —
        only statically analyzed.
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
        "flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all",
        active
          ? "bg-card text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {icon}
      {label}
    </button>
  );
}
