## 1. Create the CI workflow

- [x] 1.1 Create `.github/workflows/ci.yml` with 5 jobs (frontend-quality, contract-check, backend-quality, backend-db, preflight aggregate)
- [x] 1.2 Adjust for this project: branch `master` (not `main`), DB name `ai_interviewer_test`, no `pytest -m db` step (0 DB-marked tests)
- [x] 1.3 Sanitize: no forbidden words, no reference project names

## 2. Verify CI passes on GitHub Actions

- [x] 2.1 Commit and push to `github` remote
- [x] 2.2 Wait for the GitHub Actions run to complete
- [x] 2.3 Confirm all 5 jobs pass (or document any failures and fixes)

## 3. Sync and archive

- [x] 3.1 Sync delta specs into `openspec/specs/`
- [x] 3.2 Archive the change to `openspec/changes/archive/`
- [x] 3.3 Commit, push to both remotes (origin + github)
- [x] 3.4 Verify `openspec validate --all` and `just bootstrap-check` pass
