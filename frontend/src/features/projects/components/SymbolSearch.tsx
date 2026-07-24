"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Search } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  projectsApi,
  type SymbolItem,
} from "@/features/projects/api/projects.api";

/** Short label + color per symbol kind for the result badge. */
function kindStyle(type: string): { label: string; className: string } {
  const map: Record<string, { label: string; className: string }> = {
    class: { label: "class", className: "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300" },
    interface: { label: "interface", className: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300" },
    enum: { label: "enum", className: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300" },
    struct: { label: "struct", className: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300" },
    function: { label: "fn", className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" },
    arrow_function: { label: "fn", className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" },
    method: { label: "method", className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" },
    constant: { label: "const", className: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300" },
    variable: { label: "var", className: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300" },
    import: { label: "import", className: "bg-secondary text-muted-foreground" },
    export: { label: "export", className: "bg-secondary text-muted-foreground" },
  };
  return (
    map[type] ?? {
      label: type.replace(/_/g, " "),
      className: "bg-secondary text-muted-foreground",
    }
  );
}

export function SymbolSearch({
  projectId,
  analyzed,
}: {
  projectId: string;
  analyzed: boolean;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SymbolItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState(false);
  const reqId = useRef(0);

  // Debounced search — one request ~250ms after typing stops.
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    setTouched(true);
    const id = ++reqId.current;
    const timer = setTimeout(async () => {
      try {
        const data = await projectsApi.searchSymbols(projectId, q);
        if (id === reqId.current) {
          setResults(data.symbols);
          setTotal(data.total);
        }
      } catch {
        if (id === reqId.current) {
          setResults([]);
          setTotal(0);
        }
      } finally {
        if (id === reqId.current) setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query, projectId]);

  return (
    <div className="space-y-2.5">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            analyzed
              ? "Search symbols — e.g. login, UserService…"
              : "Analyze the code first to search symbols"
          }
          disabled={!analyzed}
          className="h-10 w-full rounded-lg border bg-card pl-9 pr-9 text-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20 disabled:cursor-not-allowed disabled:opacity-60"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {query.trim() && (
        <div className="scrollbar-slim max-h-72 overflow-y-auto rounded-lg border bg-card">
          {results.length === 0 && !loading && touched ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              No symbols match &ldquo;{query.trim()}&rdquo;.
            </p>
          ) : (
            <>
              {total > results.length && (
                <p className="border-b px-3 py-1.5 text-[11px] text-muted-foreground">
                  Showing top {results.length} of{" "}
                  <span className="font-mono tabular-nums">{total}</span> matches
                </p>
              )}
              <ul className="divide-y">
                {results.map((s) => (
                  <SymbolRow key={s.id} symbol={s} />
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function SymbolRow({ symbol: s }: { symbol: SymbolItem }) {
  const kind = kindStyle(s.symbol_type);
  const location = s.file_path
    ? `${s.file_path}:${s.line_number}`
    : `line ${s.line_number}`;
  return (
    <li className="flex items-start gap-2.5 px-3 py-2 transition-colors hover:bg-accent/5">
      <span
        className={cn(
          "mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium",
          kind.className,
        )}
      >
        {kind.label}
      </span>
      <div className="min-w-0 flex-1">
        <p className="flex items-baseline gap-1.5">
          <span className="truncate font-mono text-[13px] font-medium text-foreground">
            {s.name}
          </span>
          {s.parent_symbol && (
            <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
              in {s.parent_symbol}
            </span>
          )}
        </p>
        <p className="truncate font-mono text-[11px] text-muted-foreground" title={location}>
          {location}
        </p>
      </div>
    </li>
  );
}
