"use client";

import { cn } from "@/lib/utils";

type QuestionDisplayProps = Readonly<{
  question: string | null;
  isVisible: boolean;
}>;

export function QuestionDisplay({ question, isVisible }: QuestionDisplayProps) {
  if (!isVisible || !question) return null;

  return (
    <p
      key={question}
      className={cn(
        "text-2xl font-semibold tracking-tight text-foreground",
        "w-full text-left",
        "animate-[fade-up_200ms_ease-out_both]",
      )}
    >
      {question}
    </p>
  );
}
