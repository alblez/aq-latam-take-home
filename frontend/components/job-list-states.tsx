import { RetryButton } from "@/components/retry-button";
import { Skeleton } from "@/components/ui/skeleton";

export function JobListLoading() {
  return (
    <div className="grid grid-cols-1 gap-lg sm:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-lg border border-border bg-surface p-lg">
          <Skeleton className="mb-md h-6 w-3/4" />
          <Skeleton className="mb-sm h-4 w-full" />
          <Skeleton className="mb-lg h-4 w-2/3" />
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-28 rounded-full" />
            <Skeleton className="h-4 w-12" />
          </div>
        </div>
      ))}
      <output className="sr-only">Loading positions, please wait.</output>
    </div>
  );
}

export function JobListEmpty() {
  return (
    <section
      className="mx-auto flex w-full max-w-[520px] flex-col items-center justify-center py-2xl text-center"
      aria-labelledby="empty-heading"
    >
      <div className="mb-lg flex h-16 w-16 items-center justify-center rounded-full border border-border bg-surface">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-foreground-muted"
          aria-hidden="true"
        >
          <rect x="2" y="7" width="20" height="14" rx="2" />
          <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
        </svg>
      </div>
      <h2 id="empty-heading" className="mb-sm text-xl font-semibold tracking-[-0.01em]">
        No positions available
      </h2>
      <p className="w-full max-w-[42ch] text-sm leading-relaxed text-foreground-muted">
        There are no interview roles configured yet. Check back later or contact your administrator
        to add roles.
      </p>
    </section>
  );
}

export function JobListError({ message }: Readonly<{ message?: string }>) {
  return (
    <section
      className="mx-auto flex w-full max-w-[520px] flex-col items-center justify-center py-2xl text-center"
      aria-labelledby="error-heading"
      role="alert"
    >
      <div className="mb-lg flex h-16 w-16 items-center justify-center rounded-full bg-destructive-muted">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-destructive"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <h2 id="error-heading" className="mb-sm text-xl font-semibold tracking-[-0.01em]">
        Unable to load positions
      </h2>
      <p className="mb-lg w-full max-w-[42ch] text-sm leading-relaxed text-foreground-muted">
        {message || "Something went wrong while fetching available roles. Please try again."}
      </p>
      <RetryButton />
    </section>
  );
}
