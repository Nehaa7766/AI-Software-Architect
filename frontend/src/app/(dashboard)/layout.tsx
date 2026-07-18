"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import {
  BarChart3,
  Bell,
  Bot,
  Boxes,
  Braces,
  FolderGit2,
  LayoutDashboard,
  ListChecks,
  Loader2,
  LogOut,
  Search,
  Settings,
  Sparkles,
  Waypoints,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth/hooks/useAuth";

type NavItem = {
  href?: string;
  label: string;
  icon: typeof LayoutDashboard;
  soon?: boolean;
};

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FolderGit2 },
  { label: "AI Architecture Map", icon: Waypoints, soon: true },
  { label: "Code Intelligence", icon: Braces, soon: true },
  { label: "Agents", icon: Bot, soon: true },
  { label: "Tasks", icon: ListChecks, soon: true },
  { label: "Reports", icon: BarChart3, soon: true },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { user, loading, isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace(`/login?from=${encodeURIComponent(pathname)}`);
    }
  }, [loading, isAuthenticated, router, pathname]);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const email = user?.email ?? "";
  const initials = email.slice(0, 2).toUpperCase() || "AA";

  return (
    <div className="min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col bg-forest text-forest-foreground lg:flex">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-5 py-5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-bright/15 text-brand-bright ring-1 ring-brand-bright/30">
            <Boxes className="h-5 w-5" strokeWidth={2.2} />
          </span>
          <span className="text-[15px] font-semibold leading-tight tracking-tight">
            AI Software
            <br />
            Architect
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {NAV.map((item) => {
            const active = item.href && pathname === item.href;
            const Icon = item.icon;
            const inner = (
              <>
                <Icon className="h-[18px] w-[18px] shrink-0" />
                <span className="flex-1 truncate text-left">{item.label}</span>
                {item.soon && (
                  <span className="rounded-full bg-forest-600 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-forest-foreground/60">
                    Soon
                  </span>
                )}
              </>
            );
            const base =
              "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors";
            if (item.soon || !item.href) {
              return (
                <div
                  key={item.label}
                  className={cn(
                    base,
                    "cursor-not-allowed text-forest-foreground/45",
                  )}
                >
                  {inner}
                </div>
              );
            }
            return (
              <Link
                key={item.label}
                href={item.href}
                className={cn(
                  base,
                  active
                    ? "bg-brand-bright/15 text-white ring-1 ring-brand-bright/25"
                    : "text-forest-foreground/70 hover:bg-forest-700 hover:text-white",
                )}
              >
                {inner}
              </Link>
            );
          })}
        </nav>

        {/* AI Architect Mode card */}
        <div className="px-3 pb-3">
          <div className="dot-grid relative overflow-hidden rounded-2xl bg-forest-700 p-4 ring-1 ring-white/5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-bright" />
              <span className="text-sm font-semibold text-white">
                AI Architect Mode
              </span>
            </div>
            <div className="mt-2 flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-bright/70" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-bright" />
              </span>
              <span className="text-xs font-medium uppercase tracking-wide text-brand-bright">
                Active
              </span>
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-forest-foreground/55">
              Autonomous analysis, planning &amp; coding assistants online.
            </p>
          </div>
        </div>

        {/* User */}
        <div className="flex items-center gap-2.5 border-t border-white/5 px-4 py-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-bright/20 text-xs font-semibold text-brand-bright">
            {initials}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-white">{email}</p>
            <p className="text-[10px] text-forest-foreground/50">System Admin</p>
          </div>
          <button
            onClick={() => logout()}
            className="rounded-lg p-1.5 text-forest-foreground/60 transition-colors hover:bg-forest-700 hover:text-white"
            aria-label="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 border-b border-border/70 bg-background/85 backdrop-blur-xl">
          <div className="flex h-16 items-center gap-4 px-5 sm:px-8">
            <div className="relative hidden max-w-xl flex-1 sm:block">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Ask Architect anything — e.g. analyze auth flow, find dependencies…"
                className="h-10 w-full rounded-xl border bg-card pl-9 pr-4 text-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
              />
            </div>
            <div className="ml-auto flex items-center gap-3">
              <button
                className="relative rounded-xl border bg-card p-2 text-muted-foreground transition-colors hover:text-foreground"
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-brand-bright" />
              </button>
              <div className="flex items-center gap-2">
                <span className="grid h-9 w-9 place-items-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {initials}
                </span>
                <div className="hidden leading-tight sm:block">
                  <p className="max-w-[140px] truncate text-xs font-medium text-foreground">
                    {email}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    System Admin
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="lg:hidden"
                onClick={() => logout()}
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </header>

        <main className="px-5 py-6 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
