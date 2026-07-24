"use client";

import { useEffect, useRef, useState } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import { AlertCircle, FileCode2, Loader2 } from "lucide-react";

import { getErrorMessage } from "@/lib/axios";
import { projectsApi } from "@/features/projects/api/projects.api";

export type OpenFile = { path: string; line: number; name?: string };

// Monaco editor + namespace types kept loose to avoid pulling monaco types.
type Editor = Parameters<OnMount>[0];
type Monaco = Parameters<OnMount>[1];

export function CodeViewer({
  projectId,
  file,
}: {
  projectId: string;
  file: OpenFile | null;
}) {
  const [content, setContent] = useState("");
  const [language, setLanguage] = useState("plaintext");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const editorRef = useRef<Editor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationsRef = useRef<string[]>([]);

  // Load the requested file whenever the path changes.
  useEffect(() => {
    if (!file) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    projectsApi
      .getFile(projectId, file.path)
      .then((data) => {
        if (cancelled) return;
        setContent(data.content);
        setLanguage(data.language);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(getErrorMessage(err, "Could not open this file."));
        setContent("");
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [projectId, file?.path]); // eslint-disable-line react-hooks/exhaustive-deps

  // Jump + highlight when the target line (or freshly loaded content) changes.
  const revealLine = () => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco || !file) return;
    const line = Math.max(1, file.line || 1);
    editor.revealLineInCenter(line);
    editor.setPosition({ lineNumber: line, column: 1 });
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [
      {
        range: new monaco.Range(line, 1, line, 1),
        options: {
          isWholeLine: true,
          className: "viewer-active-line",
          linesDecorationsClassName: "viewer-active-line-margin",
        },
      },
    ]);
  };

  useEffect(() => {
    if (!loading && content) revealLine();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, content, file?.line]);

  const onMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    revealLine();
  };

  if (!file) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center text-muted-foreground">
        <FileCode2 className="h-8 w-8 opacity-50" />
        <p className="text-sm">
          Search a symbol and click a result to open its source here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* File bar */}
      <div className="flex items-center gap-2 border-b bg-card px-4 py-2.5">
        <FileCode2 className="h-4 w-4 shrink-0 text-accent" />
        <span className="truncate font-mono text-xs text-foreground" title={file.path}>
          {file.path}
        </span>
        <span className="ml-auto shrink-0 rounded bg-secondary px-1.5 py-0.5 font-mono text-[10px] tabular-nums text-muted-foreground">
          Line {file.line}
        </span>
      </div>

      {/* Editor / states */}
      <div className="relative flex-1">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/60">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}
        {error ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center">
            <AlertCircle className="h-8 w-8 text-rose-500" />
            <p className="text-sm font-medium text-foreground">
              Could not open file
            </p>
            <p className="max-w-xs text-xs text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Editor
            key={file.path}
            height="100%"
            theme="vs-dark"
            language={language}
            value={content}
            onMount={onMount}
            loading={
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            }
            options={{
              readOnly: true,
              domReadOnly: true,
              minimap: { enabled: false },
              lineNumbers: "on",
              fontSize: 13,
              fontFamily: "var(--font-mono), monospace",
              scrollBeyondLastLine: false,
              renderLineHighlight: "none",
              smoothScrolling: true,
              contextmenu: false,
              wordWrap: "on",
              automaticLayout: true,
            }}
          />
        )}
      </div>
    </div>
  );
}
