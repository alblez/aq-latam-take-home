"use client";

import { formatDate } from "@/lib/format-date";
import type { SessionSummary } from "@/types/session";

type ScoreTrendChartProps = Readonly<{
  sessions: SessionSummary[];
}>;

const DATE_OPTIONS: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };

export function ScoreTrendChart({ sessions }: ScoreTrendChartProps) {
  // Filter out sessions with null overallScore (no data to plot)
  const scoredSessions = sessions.filter(
    (s): s is SessionSummary & { overallScore: number } => s.overallScore !== null,
  );

  if (scoredSessions.length < 2) {
    return (
      <div className="flex h-40 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        <p className="text-sm text-[var(--color-foreground-muted)]">
          Complete more interviews to see trends
        </p>
      </div>
    );
  }

  const sorted = [...scoredSessions].sort(
    (a, b) => new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime(),
  );

  const width = 600;
  const height = 160;
  const padX = 48;
  const padY = 24;
  const chartW = width - padX * 2;
  const chartH = height - padY * 2;
  const maxScore = 10;

  const points: { x: number; y: number; session: (typeof sorted)[number] }[] = sorted.map(
    (s, i) => ({
      x: padX + (i / (sorted.length - 1)) * chartW,
      y: padY + chartH - (s.overallScore / maxScore) * chartH,
      session: s,
    }),
  );

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  // Y-axis ticks
  const yTicks = [0, 2.5, 5, 7.5, 10];

  return (
    <div className="w-full overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-[var(--color-foreground-muted)]">
        Score Trend
      </h3>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-auto w-full"
        role="img"
        aria-label="Score trend over time"
      >
        {/* Grid lines */}
        {yTicks.map((tick) => {
          const y = padY + chartH - (tick / maxScore) * chartH;
          return (
            <g key={tick}>
              <line
                x1={padX}
                y1={y}
                x2={padX + chartW}
                y2={y}
                stroke="var(--color-border)"
                strokeWidth={0.5}
              />
              <text
                x={padX - 8}
                y={y + 4}
                textAnchor="end"
                fontSize={10}
                fill="var(--color-foreground-muted)"
                fontFamily="var(--font-mono)"
              >
                {tick}
              </text>
            </g>
          );
        })}

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Dots */}
        {points.map((p) => (
          <circle
            key={p.session.id}
            cx={p.x}
            cy={p.y}
            r={6}
            fill="var(--color-accent)"
            stroke="var(--color-background)"
            strokeWidth={2}
          >
            <title>
              {`${p.session.overallScore.toFixed(1)} — ${formatDate(p.session.startedAt, DATE_OPTIONS)}`}
            </title>
          </circle>
        ))}

        {/* X-axis labels */}
        {points.map((p) => (
          <text
            key={`label-${p.session.id}`}
            x={p.x}
            y={height - 4}
            textAnchor="middle"
            fontSize={10}
            fill="var(--color-foreground-muted)"
            fontFamily="var(--font-mono)"
          >
            {formatDate(p.session.startedAt, DATE_OPTIONS)}
          </text>
        ))}
      </svg>
    </div>
  );
}
