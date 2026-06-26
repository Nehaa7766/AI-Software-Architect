import type { ReactNode } from "react";

/** Centered shell for the public auth pages. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-secondary/30 px-4 py-12">
      <div className="w-full max-w-md">{children}</div>
    </main>
  );
}
