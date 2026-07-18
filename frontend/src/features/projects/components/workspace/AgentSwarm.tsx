import {
  Bot,
  Compass,
  FileText,
  Rocket,
  ScanSearch,
  ShieldCheck,
  TestTube2,
} from "lucide-react";

import { cn } from "@/lib/utils";

type AgentStatus = "active" | "idle" | "standby";

const AGENTS: {
  name: string;
  icon: typeof Bot;
  status: AgentStatus;
  role: string;
}[] = [
  { name: "Architect Agent", icon: Compass, status: "active", role: "Designing system map" },
  { name: "Code Analyst", icon: ScanSearch, status: "active", role: "Parsing symbols" },
  { name: "Security Agent", icon: ShieldCheck, status: "idle", role: "Awaiting scan" },
  { name: "Test Engineer", icon: TestTube2, status: "idle", role: "Awaiting build" },
  { name: "Documenter", icon: FileText, status: "standby", role: "On standby" },
  { name: "DevOps Agent", icon: Rocket, status: "standby", role: "On standby" },
];

const STATUS: Record<AgentStatus, { label: string; dot: string; text: string }> = {
  active: {
    label: "Active",
    dot: "bg-emerald-500",
    text: "text-emerald-600 dark:text-emerald-400",
  },
  idle: {
    label: "Idle",
    dot: "bg-amber-500",
    text: "text-amber-600 dark:text-amber-400",
  },
  standby: {
    label: "Standby",
    dot: "bg-muted-foreground/50",
    text: "text-muted-foreground",
  },
};

export function AgentSwarm() {
  return (
    <section className="mt-6">
      <div className="mb-3 flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent/10 text-accent">
          <Bot className="h-4 w-4" />
        </span>
        <div>
          <h2 className="text-sm font-semibold text-foreground">
            AI Agent Swarm
          </h2>
          <p className="text-xs text-muted-foreground">
            Your autonomous engineering team
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {AGENTS.map((agent) => {
          const Icon = agent.icon;
          const s = STATUS[agent.status];
          return (
            <div
              key={agent.name}
              className="rounded-xl border bg-card p-3.5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-elevated"
            >
              <div className="mb-2.5 flex items-center justify-between">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="h-4 w-4" />
                </span>
                <span
                  className={cn(
                    "inline-flex items-center gap-1 text-[10px] font-medium",
                    s.text,
                  )}
                >
                  <span className={cn("h-1.5 w-1.5 rounded-full", s.dot)} />
                  {s.label}
                </span>
              </div>
              <p className="text-[13px] font-semibold text-foreground">
                {agent.name}
              </p>
              <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                {agent.role}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
