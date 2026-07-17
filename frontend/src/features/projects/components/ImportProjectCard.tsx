"use client";

import { useState } from "react";
import { Github, Loader2, Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

  const reset = () => {
    setFile(null);
    setRepoUrl("");
    setProgress(null);
  };

  const handleZip = async () => {
    if (!file) {
      toast.error("Choose a .zip file first.");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".zip")) {
      toast.error("Only .zip archives are accepted.");
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
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Import Project</CardTitle>
        <CardDescription>
          Upload a project ZIP or import a public GitHub repository.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex gap-2">
          <MethodButton
            active={method === "zip"}
            onClick={() => setMethod("zip")}
            icon={<Upload className="h-4 w-4" />}
            label="Upload ZIP"
          />
          <MethodButton
            active={method === "github"}
            onClick={() => setMethod("github")}
            icon={<Github className="h-4 w-4" />}
            label="GitHub Repository"
          />
        </div>

        {method === "zip" ? (
          <div className="space-y-2">
            <Label htmlFor="zip">Project archive (.zip)</Label>
            <Input
              id="zip"
              type="file"
              accept=".zip,application/zip"
              disabled={submitting}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {file && (
              <p className="text-xs text-muted-foreground">
                {file.name} · {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <Label htmlFor="repo">GitHub repository URL</Label>
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
          <div className="space-y-1">
            <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {progress < 100 ? `Uploading… ${progress}%` : "Extracting…"}
            </p>
          </div>
        )}

        <Button onClick={submit} disabled={submitting} className="w-full">
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          Import Project
        </Button>
      </CardContent>
    </Card>
  );
}

function MethodButton({
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
      className={[
        "flex flex-1 items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
        active
          ? "border-primary bg-primary/5 font-medium text-foreground"
          : "border-input text-muted-foreground hover:bg-secondary",
      ].join(" ")}
    >
      {icon}
      {label}
    </button>
  );
}
