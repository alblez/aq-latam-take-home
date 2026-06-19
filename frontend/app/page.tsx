import { History } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";
import { JobCard } from "@/components/job-card";
import { JobListEmpty, JobListError, JobListLoading } from "@/components/job-list-states";
import { Button } from "@/components/ui/button";
import { fetchJobsWithState } from "@/lib/api/jobs";

type PageProps = Readonly<{
  searchParams: Promise<{ state?: string }>;
}>;

async function JobGrid({ state }: Readonly<{ state?: string }>) {
  if (state === "loading") {
    return <JobListLoading />;
  }

  const result = await fetchJobsWithState(state);

  if (result.status === "error") {
    return <JobListError message={result.message} />;
  }

  if (result.status === "empty" || result.jobs.length === 0) {
    return <JobListEmpty />;
  }

  return (
    <ul className="card-stagger grid grid-cols-1 gap-lg sm:grid-cols-2 lg:grid-cols-3">
      {result.jobs.map((job) => (
        <li key={job.id}>
          <JobCard job={job} />
        </li>
      ))}
    </ul>
  );
}

export default async function HomePage({ searchParams }: PageProps) {
  const params = await searchParams;
  const state = params.state;

  return (
    <div className="relative min-h-dvh w-full bg-background">
      {/* Grain noise overlay */}
      <div className="grain-overlay fixed inset-0 z-[var(--z-grain)]" aria-hidden="true" />

      {/* Content */}
      <main
        id="main-content"
        className="relative z-[var(--z-content)] mx-auto max-w-[1024px] px-md pb-2xl pt-xl sm:px-lg sm:pb-[72px] sm:pt-2xl"
      >
        {/* Hero heading with brand gradient */}
        <header className="relative mb-2xl flex items-start justify-between gap-md">
          {/* Subtle radial gradient — brand warmth, landing only */}
          <div
            className="pointer-events-none absolute -top-[80px] left-1/2 -z-10 h-[400px] w-[600px] -translate-x-1/2 rounded-full opacity-60 blur-[80px] dark:hidden"
            style={{
              background:
                "radial-gradient(ellipse at center, oklch(0.94 0.03 220) 0%, transparent 70%)",
            }}
            aria-hidden="true"
          />
          <div
            className="pointer-events-none absolute -top-[80px] left-1/2 -z-10 hidden h-[400px] w-[600px] -translate-x-1/2 rounded-full opacity-40 blur-[80px] dark:block"
            style={{
              background:
                "radial-gradient(ellipse at center, oklch(0.18 0.02 220) 0%, transparent 70%)",
            }}
            aria-hidden="true"
          />
          <div>
            <h1 className="font-display text-[clamp(2rem,5vw,2.75rem)] font-normal leading-[1.08] tracking-[-0.01em] text-foreground">
              Practice before it counts
            </h1>
            <p className="mt-md max-w-[52ch] text-base leading-[1.6] text-foreground-muted">
              Pick a role, answer real interview questions, and get clear feedback on what to
              improve.
            </p>
          </div>
          <Link href="/history" className="shrink-0">
            <Button variant="ghost" size="sm">
              <History className="size-4" aria-hidden="true" />
              History
            </Button>
          </Link>
        </header>

        {/* Job grid */}
        <Suspense fallback={<JobListLoading />}>
          <JobGrid state={state} />
        </Suspense>
      </main>
    </div>
  );
}
