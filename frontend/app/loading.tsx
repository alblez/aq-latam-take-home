import { JobListLoading } from "@/components/job-list-states";

export default function Loading() {
  return (
    <main id="main-content" className="mx-auto max-w-[1024px] px-md py-xl sm:px-lg sm:py-2xl">
      <header className="mb-xl">
        <div className="h-9 w-64 animate-skeleton rounded-md bg-border" />
        <div className="mt-sm h-5 w-96 max-w-full animate-skeleton rounded-md bg-border" />
      </header>
      <JobListLoading />
    </main>
  );
}
