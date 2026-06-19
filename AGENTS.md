# AGENTS.md

Operating guide for AI agents and humans working in this repository.

## What this project is

An implementation of the AI Interviewer Platform take-home brief (see
[`docs/home_test_requirements.md`](docs/home_test_requirements.md) and [README.md](README.md)):
a voice-driven interview app with a deterministic decision panel, role question packs, and
replay/analytics. The work is planned and tracked with **OpenSpec**.

## Methodology: OpenSpec

All work flows through OpenSpec changes. **One change = one unit of work.** Do not create
planning documents outside of what OpenSpec generates.

```
/opsx:propose <name>   →  /opsx:apply  →  /opsx:sync  →  /opsx:archive
```

- `openspec/specs/` — the source of truth for current behavior, populated when changes archive.
- `openspec/changes/<name>/` — one folder per unit of work: `proposal.md`, `design.md`
  (when the change is cross-cutting or non-obvious), delta `specs/`, and `tasks.md`.
- Author artifacts via the CLI templates: `openspec new change <name>`, then
  `openspec instructions <artifact> --change <name> --json`. Validate with
  `openspec validate --all`. Inspect with `openspec list` / `openspec show <name>`.
- Delta specs use `## ADDED|MODIFIED|REMOVED Requirements`, each `### Requirement:` with
  `SHALL`/`MUST` and at least one `#### Scenario:` (exactly four `#`).
- Each change maps to brief requirements in its proposal's **Requirements Coverage** section,
  so the specs themselves are the requirement-trace artifact.

## Planned changes

| Change | Purpose |
|---|---|
| `implement-backend` | First: FastAPI skeleton + persistence, a thin vertical slice, then the interview engine, decision panel, evaluation, and history. Emits `shared/contract.yaml`. |
| `define-api-contract` | Stabilizes the emitted contract, generates the frontend types, and wires the drift checks. |
| `implement-frontend` | Next.js against the generated contract types: job selection, voice Interview Room, decision panel, review/history. |
| `prepare-deployment` | Public hosted deployment, end to end (required by the brief). |

Deliver a thin hosted vertical slice first (one role → interview → evaluation, deployed),
then add depth and the stretch goals.

## Backend-first sequencing

- The backend is implemented first and **emits** `shared/contract.yaml` from its runtime OpenAPI.
- `define-api-contract` then stabilizes that contract and generates the frontend types; the drift
  gate keeps the backend runtime OpenAPI and the committed contract identical, with
  `contract-types:check` guarding the frontend side.
- The frontend is built against the generated types. Mock mode is a local development aid only;
  hosted environments set `NEXT_PUBLIC_USE_MOCK=false` and use the deployed backend.
- Once stabilized, the contract changes only through a new OpenSpec change.

## Harness

Standardized on **opencode**, with **Claude Code** as a co-driver. OpenSpec slash commands
and skills are committed under `.opencode/` and `.claude/`. Regenerate them after upgrading
OpenSpec with `openspec update`.

## Conventions

- **Conventional commits**, one line: `type(scope): subject`. Commit authorship is the
  repository owner only — **do not add AI co-author trailers.**
- `just bootstrap-check` is the day-zero gate. `just quality` / `just preflight` are the full
  project gates and remain authoritative even before all tracks land.
- Heavy checks (mutation testing, contract fuzzing, DB smoke, dependency audit) are
  manual/final gates; they do not block day-one progress.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy + Alembic, PostgreSQL, OpenRouter LLM.
  Gates: ruff, pyright, pytest, hypothesis, coverage, deptry, sqlfluff (+ mutmut, schemathesis, pip-audit as final gates).
- **Frontend**: Next.js 16, React 19, TypeScript (strict), Tailwind, Radix/shadcn.
  Gates: tsc, Biome, knip, Vitest, `openapi-typescript` codegen + drift check.
- **Repo**: justfile (task runner), lefthook (git hooks), gitleaks (secrets), redocly (contract lint).
