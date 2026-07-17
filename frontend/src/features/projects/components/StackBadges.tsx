import type { DetectedStack } from "@/features/projects/api/projects.api";

function Pill({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone: "lang" | "framework" | "pm";
}) {
  const styles = {
    lang: "bg-indigo-100 text-indigo-800",
    framework: "bg-sky-100 text-sky-800",
    pm: "bg-slate-100 text-slate-700",
  }[tone];
  return (
    <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${styles}`}>
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
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      {topLanguages.map((l) => (
        <Pill key={l.language} tone="lang">
          {l.language} {l.percentage}%
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
