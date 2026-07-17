import { api } from "@/lib/axios";

export type ImportSource = "ZIP" | "GITHUB";
export type ProjectStatus = "UPLOADED" | "EXTRACTED" | "FAILED";

export interface LanguageStat {
  language: string;
  files: number;
  bytes: number;
  percentage: number;
}

export interface DetectedStack {
  primary_language: string | null;
  languages: LanguageStat[];
  frameworks: string[];
  package_managers: string[];
  total_files: number;
  total_source_bytes: number;
}

export interface Project {
  id: string;
  project_name: string;
  source_type: ImportSource;
  source_location: string;
  status: ProjectStatus;
  error_message: string | null;
  primary_language: string | null;
  stack: DetectedStack | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export interface MessageResponse {
  message: string;
}

export const projectsApi = {
  list: () =>
    api.get<ProjectListResponse>("/projects").then((r) => r.data),

  get: (id: string) =>
    api.get<Project>(`/projects/${id}`).then((r) => r.data),

  uploadZip: (
    file: File,
    onProgress?: (percent: number) => void,
  ) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<Project>("/projects/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (onProgress && e.total) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        },
      })
      .then((r) => r.data);
  },

  importGithub: (repoUrl: string, branch?: string) =>
    api
      .post<Project>("/projects/github", {
        repo_url: repoUrl,
        branch: branch || null,
      })
      .then((r) => r.data),

  detect: (id: string) =>
    api.post<Project>(`/projects/${id}/detect`).then((r) => r.data),

  remove: (id: string) =>
    api.delete<MessageResponse>(`/projects/${id}`).then((r) => r.data),
};
