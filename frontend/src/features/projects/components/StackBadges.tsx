import type { DetectedStack } from "@/features/projects/api/projects.api";

function Pill({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone: "lang" | "framework" | "pm";
}) {
  const styles = {
    lang: "bg-indigo-50 text-indigo-700 ring-indigo-600/15 dark:bg-indigo-500/10 dark:text-indigo-300 dark:ring-indigo-400/20",
    framework:
      "bg-sky-50 text-sky-700 ring-sky-600/15 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-400/20",
    pm: "bg-secondary text-secondary-foreground ring-border",
  }[tone];
  return (
    <span
      className={`rounded-md px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset ${styles}`}
    >
      {children}
    </span>
  );
}

export function StackBadges({ stack }: { stack: DetectedStack | null }) {
  if (!stack || stack.languages.length === 0) {
    return (
      <p className="mt-2 text-xs text-muted-foreground">No stack detected.</p>
    );
  }
  // Show the top few languages by share, then frameworks, then package managers.
  const topLanguages = stack.languages.slice(0, 4);
  return (
    <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
      {topLanguages.map((l) => (
        <Pill key={l.language} tone="lang">
          {l.language}{" "}
          <span className="font-mono tabular-nums opacity-70">
            {l.percentage}%
          </span>
        </Pill>
      ))}
      {stack.frameworks.map((f) => (
        <Pill key={f} tone="framework">
          {f}
        </Pill>
      ))}
      {stack.package_managers.map((p) => (
        <Pill key={p} tone="pm">
          {p}
        </Pill>
      ))}
    </div>
  );
}
