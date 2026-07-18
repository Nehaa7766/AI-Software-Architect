/** Projects Workspace hero — title block + a blueprint line-art illustration. */
export function WorkspaceHero() {
  return (
    <div className="relative mb-6 overflow-hidden rounded-2xl border bg-card px-6 py-7 shadow-sm sm:px-8">
      <div className="relative z-10 max-w-xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-accent">
          Welcome back, Architect
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Projects Workspace
        </h1>
        <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
          Import, analyze and understand any codebase with AI-powered deep
          architecture intelligence.
        </p>
      </div>

      {/* Blueprint illustration */}
      <Blueprint className="pointer-events-none absolute -right-6 top-1/2 hidden h-[135%] -translate-y-1/2 opacity-90 md:block" />
      {/* Soft green wash */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(40rem 30rem at 95% 20%, hsl(142 60% 45% / 0.08), transparent 60%)",
        }}
        aria-hidden
      />
    </div>
  );
}

function Blueprint({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 260 200"
      fill="none"
      className={className}
      aria-hidden
    >
      <g
        stroke="hsl(146 46% 32%)"
        strokeWidth="1.1"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.55"
      >
        {/* ground grid */}
        <path d="M20 150 L130 200 L240 150 L130 100 Z" opacity="0.35" />
        {/* main tower */}
        <path d="M92 120 L92 52 L130 34 L168 52 L168 120 L130 138 Z" />
        <path d="M92 52 L130 70 L168 52 M130 70 L130 138" />
        {/* floor lines */}
        <path d="M92 74 L130 92 L168 74" opacity="0.7" />
        <path d="M92 96 L130 114 L168 96" opacity="0.7" />
        {/* left low block */}
        <path d="M44 138 L44 108 L78 92 L110 108 L110 130" opacity="0.8" />
        <path d="M44 108 L78 124 L78 92 M78 124 L110 108" opacity="0.8" />
        {/* right block */}
        <path d="M170 120 L200 106 L232 122 L232 150 L200 164 L170 150 Z" opacity="0.8" />
        <path d="M200 106 L200 164 M170 120 L200 134 L232 122" opacity="0.7" />
      </g>
      {/* accent nodes */}
      <g fill="hsl(142 64% 50%)">
        <circle cx="130" cy="34" r="2.6" />
        <circle cx="78" cy="92" r="2.2" />
        <circle cx="200" cy="106" r="2.2" />
      </g>
    </svg>
  );
}
