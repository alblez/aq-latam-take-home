"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { createSession } from "@/lib/api/jobs";
import { getOrCreateOwnerId } from "@/lib/owner-id";
import type { Job } from "@/types/job";

// ---------------------------------------------------------------------------
// JobCard — client component that creates a session then redirects
// ---------------------------------------------------------------------------
export function JobCard({ job }: Readonly<{ job: Job }>) {
  const router = useRouter();
  const [isPending, setIsPending] = useState(false);

  const handleClick = useCallback(
    async (e: React.MouseEvent) => {
      e.preventDefault();
      if (isPending) return;

      setIsPending(true);
      try {
        // Owner flows via X-Owner-Id header in apiCall — no ownerId param needed
        getOrCreateOwnerId(); // ensure owner ID exists in localStorage for apiCall
        const result = await createSession(job.id);

        if (result.status === "ok") {
          router.push(`/interview/${result.session.id}`);
        } else {
          // Surface error — stay on page, allow retry
          console.error("Session creation failed:", result.message);
          setIsPending(false);
        }
      } catch {
        setIsPending(false);
      }
    },
    [job.id, isPending, router],
  );

  return (
    <a
      href={`/interview/demo-${job.id}`}
      onClick={handleClick}
      aria-label={`Begin interview: ${job.title}`}
      aria-disabled={isPending}
      className="group block rounded-lg transition-[box-shadow,translate,scale] duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] hover:shadow-hover motion-safe:hover:-translate-y-px focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent motion-safe:active:scale-[0.98]"
    >
      <Card className="h-full transition-colors duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:border-accent/40">
        <CardHeader>
          <CardTitle>{job.title}</CardTitle>
          <CardDescription>{job.description}</CardDescription>
        </CardHeader>
        <CardFooter className="justify-between">
          <Badge variant="accent">{job.competencyCount} competencies</Badge>
          <span className="inline-flex items-center gap-xs text-sm font-semibold text-accent transition-colors duration-150 group-hover:text-accent-foreground">
            {isPending ? "Starting\u2026" : "Begin"}
            {!isPending && (
              <svg
                className="h-4 w-4 motion-safe:transition-transform motion-safe:duration-200 motion-safe:ease-[cubic-bezier(0.16,1,0.3,1)] motion-safe:group-hover:translate-x-0.5"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M13.75 6.75L19.25 12L13.75 17.25"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M19 12H4.75"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </span>
        </CardFooter>
      </Card>
    </a>
  );
}
