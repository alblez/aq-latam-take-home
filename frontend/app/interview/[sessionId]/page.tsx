"use client";

import { use } from "react";
import { InterviewRoom } from "@/components/interview/interview-room";

type InterviewPageProps = Readonly<{
  params: Promise<{ sessionId: string }>;
}>;

export default function InterviewPage({ params }: InterviewPageProps) {
  const { sessionId } = use(params);
  return <InterviewRoom sessionId={sessionId} />;
}
