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

export interface TreeNode {
  name: string;
  path: string;
  type: "dir" | "file";
  size_bytes: number | null;
  language: string | null;
  children: TreeNode[] | null;
}

export interface ProjectTree {
  root: TreeNode;
  total_files: number;
  total_dirs: number;
  truncated: boolean;
}

export interface FileSymbolCounts {
  functions: number;
  methods: number;
  classes: number;
  total: number;
}

export interface SymbolsByFile {
  project_id: string;
  files: Record<string, FileSymbolCounts>;
  total_symbols: number;
}

export interface SymbolItem {
  id: string;
  file_id: string;
  file_path: string | null;
  name: string;
  symbol_type: string;
  language: string;
  parent_symbol: string | null;
  visibility: string;
  signature: string | null;
  line_number: number;
}

export interface SymbolListResponse {
  symbols: SymbolItem[];
  total: number;
  by_type: Record<string, number>;
}

export interface SymbolCounts {
  classes: number;
  interfaces: number;
  enums: number;
  functions: number;
  methods: number;
  variables: number;
  constants: number;
  imports: number;
  exports: number;
  decorators: number;
  comments: number;
  docstrings: number;
}

export interface ParseSummary {
  project_id: string;
  status: string;
  files_total: number;
  files_parsed: number;
  files_skipped: number;
  files_failed: number;
  total_symbols: number;
  symbols: SymbolCounts;
  by_type: Record<string, number>;
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

  tree: (id: string) =>
    api.get<ProjectTree>(`/projects/${id}/tree`).then((r) => r.data),

  parse: (id: string) =>
    api.post<ParseSummary>(`/projects/${id}/parse`).then((r) => r.data),

  symbolsByFile: (id: string) =>
    api
      .get<SymbolsByFile>(`/projects/${id}/symbols/by-file`)
      .then((r) => r.data),

  searchSymbols: (id: string, q: string, limit = 30) =>
    api
      .get<SymbolListResponse>(`/projects/${id}/symbols`, {
        params: { q, limit },
      })
      .then((r) => r.data),

  remove: (id: string) =>
    api.delete<MessageResponse>(`/projects/${id}`).then((r) => r.data),
};
