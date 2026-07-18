import { Activity } from "lucide-react";

/**
 * Architecture Health module. The scores are illustrative — there is no health
 * scoring backend yet — so it renders a fixed, representative snapshot.
 */
const METRICS = [
  { label: "Structure Quality", value: 94 },
  { label: "Code Maintainability", value: 87 },
  { label: "Security Score", value: 89 },
  { label: "Performance Score", value: 80 },
  { label: "Test Coverage", value: 66 },
];

const OVERALL = 92;

export function ArchitectureHealth() {
  return (
    <div className="rounded-2xl bg-forest p-5 text-forest-foreground shadow-elevated">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-brand-bright" />
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-forest-foreground/70">
          Architecture Health
        </h3>
      </div>

      <div className="mb-5 flex justify-center">
        <Gauge value={OVERALL} />
      </div>

      <ul className="space-y-3">
        {METRICS.map((m) => (
          <li key={m.label}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-forest-foreground/75">{m.label}</span>
              <span className="font-mono font-medium tabular-nums text-white">
                {m.value}%
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-brand-bright"
                style={{ width: `${m.value}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Gauge({ value }: { value: number }) {
  const r = 46;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - value / 100);
  return (
    <div className="relative h-32 w-32">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="hsl(0 0% 100% / 0.1)"
          strokeWidth="9"
        />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="hsl(var(--brand-bright))"
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-3xl font-bold tabular-nums text-white">
          {value}
          <span className="text-lg">%</span>
        </span>
        <span className="text-[10px] uppercase tracking-wide text-forest-foreground/60">
          Overall
        </span>
      </div>
    </div>
  );
}
