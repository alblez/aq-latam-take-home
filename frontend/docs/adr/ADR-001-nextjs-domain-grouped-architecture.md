# ADR-001: Next.js Domain-Grouped Architecture

## Decision

Keep `app/`, `components/`, `hooks/`, `lib/`, `types/` at the frontend app root (`frontend/`). Components grouped by domain (`interview/`, `results/`, `history/`, `shared/`, `ui/`). No Feature-Sliced Design, Clean Architecture, or `features/` wrapper.

## Context

- 5 routes, 3 domains (interview, results, history), solo developer, 4-hour budget.
- FSD creators explicitly state threshold is 20+ features for the investment to pay off.
- Clean Architecture protects domain logic from framework changes — this frontend HAS no domain logic. FastAPI backend owns interview controller, competency model, evaluation, persistence.
- Feature-based `features/` directory adds one nesting level for zero cognitive gain at 3 features.
- Current structure already IS feature organization: domain-grouped components co-located by business context.

## Consequences

- Agents must not propose folder migrations to FSD, Clean Architecture, or feature-based patterns.
- New components go in their domain folder: `components/interview/`, `components/results/`, `components/history/`.
- Cross-cutting components (error, loading, empty states) go in `components/shared/`.
- Design system primitives (shadcn) go in `components/ui/`.
- Route files stay thin (composition nodes, not orchestration).
- No `src/` wrapper, no barrel exports, no DI containers.
