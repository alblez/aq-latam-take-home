// Shared date formatting helpers that guard against invalid/missing inputs.
// `Session.startedAt` is optional and backend values can be empty/malformed;
// `new Date("")`/`new Date(undefined)` yields an Invalid Date whose
// toLocaleDateString returns the literal "Invalid Date" string. Guard first.

const EM_DASH = "—";

export function formatDate(
  iso: string | null | undefined,
  options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" },
): string {
  if (!iso) return EM_DASH;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? EM_DASH : d.toLocaleDateString("en-US", options);
}
