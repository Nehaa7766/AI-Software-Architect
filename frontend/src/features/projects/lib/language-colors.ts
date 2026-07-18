/** Canonical accent color per language, for rails, dots and bars. */
const LANGUAGE_HEX: Record<string, string> = {
  Python: "#3b82f6",
  JavaScript: "#eab308",
  TypeScript: "#3178c6",
  Java: "#f97316",
  Go: "#22d3ee",
  Rust: "#f43f5e",
  "C#": "#8b5cf6",
  PHP: "#6366f1",
  Ruby: "#ef4444",
  Kotlin: "#a855f7",
  Swift: "#fb7185",
  C: "#64748b",
  "C++": "#ec4899",
  HTML: "#f97316",
  CSS: "#0ea5e9",
  Shell: "#10b981",
  SQL: "#14b8a6",
};

const FALLBACK = "#8b5cf6";

/** A stable color for a language label (falls back to the brand violet). */
export function languageColor(language: string | null | undefined): string {
  if (!language) return FALLBACK;
  return LANGUAGE_HEX[language] ?? FALLBACK;
}
