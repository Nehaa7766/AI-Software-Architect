"use client";

import { useMemo, useState } from "react";
import { ChevronRight, File, Folder, FolderOpen } from "lucide-react";

import { cn } from "@/lib/utils";
import { languageColor } from "@/features/projects/lib/language-colors";
import type {
  FileSymbolCounts,
  TreeNode,
} from "@/features/projects/api/projects.api";

type CountsMap = Record<string, FileSymbolCounts>;

function formatBytes(bytes: number | null): string {
  if (bytes === null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Sum every file symbol count under a directory (recursive) for its badge. */
function aggregate(node: TreeNode, counts: CountsMap): FileSymbolCounts {
  if (node.type === "file") {
    return (
      counts[node.path] ?? { functions: 0, methods: 0, classes: 0, total: 0 }
    );
  }
  const acc: FileSymbolCounts = {
    functions: 0,
    methods: 0,
    classes: 0,
    total: 0,
  };
  for (const child of node.children ?? []) {
    const c = aggregate(child, counts);
    acc.functions += c.functions;
    acc.methods += c.methods;
    acc.classes += c.classes;
    acc.total += c.total;
  }
  return acc;
}

/** "N fn" badge = standalone functions + methods (what most people mean). */
function SymbolBadge({ counts }: { counts: FileSymbolCounts }) {
  const fns = counts.functions + counts.methods;
  if (fns === 0 && counts.classes === 0) return null;
  return (
    <span className="flex shrink-0 items-center gap-1 font-mono tabular-nums">
      {fns > 0 && (
        <span
          className="rounded bg-emerald-50 px-1 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/15 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-400/20"
          title={`${counts.functions} functions, ${counts.methods} methods`}
        >
          {fns} fn
        </span>
      )}
      {counts.classes > 0 && (
        <span
          className="rounded bg-violet-50 px-1 text-[10px] font-medium text-violet-700 ring-1 ring-inset ring-violet-600/15 dark:bg-violet-500/10 dark:text-violet-400 dark:ring-violet-400/20"
          title={`${counts.classes} classes`}
        >
          {counts.classes} cls
        </span>
      )}
    </span>
  );
}

function TreeItem({
  node,
  depth,
  counts,
}: {
  node: TreeNode;
  depth: number;
  counts: CountsMap;
}) {
  // Top level starts expanded so the structure is visible at a glance.
  const [open, setOpen] = useState(depth < 1);
  const indent = { paddingLeft: `${depth * 14 + 10}px` };

  if (node.type === "file") {
    const fileCounts = counts[node.path];
    return (
      <div
        style={indent}
        className="flex items-center gap-2 rounded-md py-1 pr-2.5 text-[13px] transition-colors hover:bg-accent/5"
        title={node.path}
      >
        {node.language ? (
          <span
            className="h-2 w-2 shrink-0 rounded-[3px]"
            style={{ backgroundColor: languageColor(node.language) }}
          />
        ) : (
          <File className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70" />
        )}
        <span className="truncate font-mono text-foreground/90">
          {node.name}
        </span>
        <span className="ml-auto flex shrink-0 items-center gap-2">
          {fileCounts && <SymbolBadge counts={fileCounts} />}
          <span className="font-mono text-[10px] tabular-nums text-muted-foreground/70">
            {formatBytes(node.size_bytes)}
          </span>
        </span>
      </div>
    );
  }

  const children = node.children ?? [];
  const dirCounts = aggregate(node, counts);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={indent}
        className="flex w-full items-center gap-1.5 rounded-md py-1 pr-2.5 text-[13px] transition-colors hover:bg-accent/5"
        title={node.path}
      >
        <ChevronRight
          className={cn(
            "h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform duration-150",
            open && "rotate-90",
          )}
        />
        {open ? (
          <FolderOpen className="h-3.5 w-3.5 shrink-0 text-accent" />
        ) : (
          <Folder className="h-3.5 w-3.5 shrink-0 text-accent/80" />
        )}
        <span className="truncate font-medium text-foreground">
          {node.name}
        </span>
        <span className="ml-auto flex shrink-0 items-center gap-2">
          <SymbolBadge counts={dirCounts} />
          <span className="font-mono text-[10px] tabular-nums text-muted-foreground/70">
            {children.length}
          </span>
        </span>
      </button>
      {open &&
        children.map((child) => (
          <TreeItem
            key={child.path}
            node={child}
            depth={depth + 1}
            counts={counts}
          />
        ))}
    </div>
  );
}

export function FileTree({
  root,
  counts = {},
}: {
  root: TreeNode;
  counts?: CountsMap;
}) {
  // Render the root's children directly (skip the redundant root folder row).
  const items = useMemo(() => root.children ?? [], [root]);
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No files found.</p>;
  }
  return (
    <div className="scrollbar-slim max-h-96 overflow-auto rounded-lg border bg-card p-1 shadow-subtle">
      {items.map((child) => (
        <TreeItem key={child.path} node={child} depth={0} counts={counts} />
      ))}
    </div>
  );
}
