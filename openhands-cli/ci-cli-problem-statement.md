# openhands-cli: CI and Release Pain Points (Problem Statement)

Context: openhands-cli is a self-contained CLI that lives as a subdirectory inside the odie-cli repository. The current CI and release setup is optimized for the broader project, which creates friction for the CLI’s lifecycle.


## Repository overview (basics we know)
- Repository: odie-cli (monorepo-style)
- Two distinct projects live here:
  - OpenHands Web App ("App"): large, multiple workflows, Python (poetry), frontend with Husky hooks
  - openhands-cli ("CLI"): self-contained subproject under `openhands-cli/`, uses uv, has its own pyproject, tests, and build tooling
- Current CLI state: several releases (around v1.0.6—verify exact tag). These were painful: ~2 hours waiting for unrelated workflows to complete.
- There may already be CLI-specific workflows in `.github/workflows/`. If they exist, start from those rather than inventing new ones.
- Key objective: enable a fast, maintainable, CLI-scoped CI/release flow without breaking or regressing the App.

## Guiding principles
- Investigate first; don’t over-design. Prefer incremental, reversible changes.
- Reuse existing CLI workflows if present; avoid inventing new pipelines unless necessary.
- Make it easy for CLI maintainers (maintenance cost is the top acceptance criterion).
- Avoid breaking the App. Isolation via path/tag filters and conditional checks.
- Ensure local DX parity: CLI maintainers should run the same checks locally via uv without needing poetry.

## Workflow inventory (current findings)
- .github/workflows/cli-build-binary-and-optionally-release.yml
  - Purpose: CLI binary build (uv/pyinstaller) and optional GitHub Release
  - Triggers: push on main; tags matching "*-cli"; PRs touching `openhands-cli/**`
  - Notes: Builds on ubuntu-22.04 and macOS; uploads artifacts; assembles release assets and creates release on tag; still fires on every push to `main` even when no CLI files changed because the push trigger lacks `paths:` guards
- .github/workflows/pypi-release.yml
  - Purpose: Publish to PyPI (App server via Poetry; CLI via uv)
  - Triggers: push on any tag; workflow_dispatch with reason: app server | cli
  - Notes: Job "release-cli" runs only for CLI: tags containing "-cli" or manual reason=cli; uv build + uv publish under `openhands-cli/`
- .github/workflows/py-tests.yml
  - Purpose: Run Python tests across projects
  - Triggers: push on main; all pull_request events (no path filtering)
  - Jobs: test-on-linux (Poetry, App), test-on-windows (Poetry, App), test-enterprise, test-cli-python (uv, CLI)
  - Observation: Heavy and always-on; likely a major contributor to long waits on CLI-only PRs
- .github/workflows/lint.yml
  - Purpose: Lint frontend and Python across projects
  - Triggers: push on main; all pull_request events (no path filtering)
  - Jobs: lint-frontend (npm/i18n/tsc), lint-python (pre-commit root), lint-enterprise-python, lint-cli-python (pre-commit in `openhands-cli/`)
  - Observation: Always-on; should be path-filtered so CLI-only PRs run only lint-cli-python
- .github/workflows/ghcr-build.yml (name: Docker)
  - Purpose: Build and push App and runtime Docker images
  - Triggers: push on main; tags; all pull_request events
  - Observation: Heavy; should be skipped when only `openhands-cli/**` changes
- .github/workflows/e2e-tests.yml
  - Purpose: End-to-end tests with Playwright
  - Triggers: PRs labeled `end-to-end`; workflow_dispatch
  - Observation: Heavy but opt-in; not a blocker for CLI-only unless labeled
- Other workflows (mostly scoped):
  - fe-unit-tests.yml (always on main; PR path filter `frontend/**`)
  - enterprise-check-migrations.yml (paths enterprise/migrations/**)
  - enterprise-preview.yml (label deploy; remote trigger)
  - ui-build.yml, npm-publish-ui.yml (paths openhands-ui/**)
  - mdx-lint.yml (paths docs/**/*.mdx)
  - vscode-extension-build.yml (paths under VSCode integration and tag ext-v*)
  - dispatch-to-docs.yml (docs/** on main)
  - lint-fix.yml (PR label `lint-fix`; auto-commits)
  - check-package-versions.yml (ensures Poetry lock alignment)
  - clean-up.yml, stale.yml (maintenance)


## Additional repository context
- Root `AGENTS.md` confirms odie-cli hosts multiple deliverables: legacy `openhands` server (V0), new app server (`app`/runtime under `openhands/`), `frontend/`, `enterprise/`, `microagents/`, and `openhands-ui/`.
- The top-level Makefile, Poetry config, and Husky hooks are optimized for the App stack; CLI lives in `openhands-cli/` with its own `pyproject.toml`, `Makefile`, and uv-based tooling.
- `openhands-cli/README.md` keeps local DX simple (`make install`, `make run`, `./build.sh --install-pyinstaller`); align any CI changes with these documented entrypoints.
- Shared configs sit in `dev_config/` (pre-commit, mypy, ruff). CLI inherits these when workflows run from the repo root, which is why pre-commit currently expects Poetry even for CLI-only diffs.
- Runtime artifacts such as `workspace/` and `logs/` appear at both root and CLI level; ensure CLI-specific automation ignores root-level transient folders to avoid cross-project contamination.
- Task tracking uses Beads (`bd`); `.beads/issues.jsonl` is the git-tracked source, while `.beads/*.db` are local SQLite files and must remain uncommitted.

## Baseline governance status
- Branch protection endpoint (`branches/main/protection`) returns `404 Not Found` even with a personal token, which likely means branch protection is managed via organization-level permissions we do not possess. Coordination with a repo admin is required to list required status checks.
- Repository ruleset `main` (`rulesets/575982`) targets the default branch but has enforcement currently disabled. Active rules forbid branch deletion and force non-fast-forward merges, plus require a single PR approval; no path-conditional checks are enforced via rulesets today.
- Observed required checks (from CLI release PR 1.0.7) indicate the following workflows must succeed before merge: `lint.yml` jobs (frontend, python, enterprise, CLI), `py-tests.yml` jobs (Linux/App, Enterprise, CLI, coverage comment), `ghcr-build.yml` matrix (define-matrix, Build App Image, Build Runtime Image for nikolaik & ubuntu, Push Enterprise Image), runtime test composites (`RT Unit Tests` variants, `All Runtime Tests Passed`), `check-package-versions`, and the CLI-specific jobs in `cli-build-binary-and-optionally-release` and `pypi-release`. Optional workflows like enterprise preview, e2e-tests, and auto-fix were skipped on that PR.
- CLI release flow (current state):
  - GitHub Releases: `.github/workflows/cli-build-binary-and-optionally-release.yml` runs on every push to `main`, on PRs touching `openhands-cli/**`, and on any tag containing `-cli`. The release job drafts a release and uploads macOS/Linux binaries whenever a `*-cli` tag is pushed.
  - PyPI: `.github/workflows/pypi-release.yml` contains an `release-cli` job gated to tags containing `-cli` or manual `workflow_dispatch` with `reason=cli`. It rebuilds the wheel via `uv build` (after clearing `dist/`) and publishes with `uv publish`.
  - Manual steps observed from README/workflows: maintainers bump version in `pyproject.toml`, create a tag with `-cli`, push to origin, then wait for shared workflows (`lint`, `py-tests`, `ghcr-build`, etc.) to succeed before the CLI-specific release jobs complete. Total elapsed time reportedly exceeds two hours because App workflows must finish first.
- Tag discovery: upstream tags now fetched locally, showing the canonical CLI sequence `1.0.0-cli` through `1.0.7-cli`. Align any new automation with this suffix-based convention.

## Workflow scoping gaps (current)
- `py-tests.yml`: triggers on all pushes/PRs with no path guards. The workflow spins up four heavy jobs (App Linux, App Windows, Enterprise, CLI) and merges coverage before commenting. Action: introduce a `dorny/paths-filter` or similar gate so App/Enterprise jobs skip when changes are limited to `openhands-cli/**`, while retaining the CLI test job.
- `lint.yml`: also unguarded. Even CLI-only diffs run frontend lint (npm install + TypeScript build) and Poetry-based Python lint. Action: add path filters so only `lint-cli-python` executes for CLI changes; consider moving shared config into a matrix keyed by path filters.
- `ghcr-build.yml`: always runs on pushes, tags, and PRs. Building/pushing both app and runtime images is unnecessary for CLI-only edits. Action: add `paths-ignore: ['openhands-cli/**']` (or positive includes for app/runtime directories) and ensure branch protections don’t require these checks for CLI paths.
- `cli-build-binary-and-optionally-release.yml`: valuable but still fires on any push to `main` even if the diff is outside `openhands-cli/`. Action: add `paths:` to the push trigger so the binary job only runs when CLI code changes or CLI tags land.
- `check-package-versions.yml` and other lightweight workflows (e.g., docs, mdx) are low-cost but still execute. Optional: add `paths-ignore: ['openhands-cli/**']` if we want zero noise on CLI PRs.
- Update (Nov 2025): Path filters now guard `lint.yml`, `py-tests.yml`, and `ghcr-build.yml`, skipping non-CLI jobs when only `openhands-cli/**` (or shared config) changes. These workflows still run on `main`, tags, or manual dispatch to protect app releases.

## Tagging and release-note observations
- Expected tag format: verified after fetching upstream—CLI releases use bare semantic versions suffixed with `-cli` (e.g., `1.0.7-cli`). Any automation should rely on `*-cli` filters and avoid introducing additional prefixes.
- GitHub release generation: `cli-build-binary-and-optionally-release.yml` creates draft releases via `softprops/action-gh-release` without a custom `body`. Maintainers must finalize notes manually, and generated notes still aggregate commits from the entire monorepo.
- PyPI publishing relies on the same tag signal as GitHub releases. Any deviation in tag naming would silently skip publishing because the `release-cli` job is gated on `contains(github.ref, '-cli')`.
- The repo history shows commits like “CLI release 1.0.7 (#11712)” updating only `openhands-cli` metadata, but no lightweight changelog accompanies them. Consider adding a CLI-specific CHANGELOG or release-please manifest so release notes remain scoped even when using draft releases.
- Fast validation: `cli-build-binary-and-optionally-release.yml` now supports `workflow_dispatch` with `fast=true` to run a Linux-only pytest smoke without PyInstaller packaging, reducing iteration time.

## Local DX gaps & follow-up actions
- Husky/pre-commit: `frontend/.husky/pre-commit` always runs frontend lint-staged + Poetry-based pre-commit, blocking CLI-only commits. Implement the path guard described in the appendix, then consider a dedicated `openhands-cli/.pre-commit-config.yaml` powered by uv for contributors who want hooks.
- Canonical local checks: codify `uv run ruff check .`, `uv run ruff format openhands_cli/`, `uv run mypy openhands_cli`, and `uv run pytest` in CLI docs (README + AGENTS). Ensure any CI additions reuse these commands to keep parity.
- Artifact hygiene: make sure CLI tooling ignores root-level `workspace/` and `logs/` directories to avoid cross-project noise in lint/test tooling.
- Task tracking: Beads (`bd`) manages work items; protect `.beads/*.db` via `.gitignore` (already present) and only commit `.beads/issues.jsonl` after updates.


## Problem summary

1) Release visibility and notes
- Mixed release streams: CLI executables are uploaded to the same Releases page as the OH App, so it’s hard to identify the latest CLI release at a glance.
- Auto-generated release notes are not project-scoped and include commits from all projects in the repo. CLI-specific changes get buried. (Monorepo-aware tools like release-please can help scope notes per project.)

2) CI coupling and latency
- Releasing the CLI requires waiting for all OH App CI workflows to complete. These workflows are numerous and sometimes flaky, which delays CLI releases and wastes maintainer time.

3) Tooling and local developer experience
- Test coverage, linting, and related checks are wired with workarounds to simulate per-project jobs within a single repo. This is brittle.


- As a result, running lint/format/test locally for only the CLI is cumbersome and error-prone.

4) Versioning and tagging
- Multiple tag conventions coexist (e.g., `X.Y.Z` vs `X.Y.Z-cli`), which complicates automation, discovery of the “latest” CLI version, and tooling that infers version numbers.


5) Change risk visibility and failure attribution
- It’s hard to know, ahead of a release, whether pending changes will break the CLI because signals (commits, CI jobs, release notes) are mixed across projects.
- When breakage occurs, root cause is difficult to pinpoint: shared pipelines and cross-project history obscure which change introduced the regression.

## Discussion points and potential directions
- There are workarounds and tools that could mitigate these problems and are worth discussing:
  - Monorepo-aware release tooling (e.g., release-please) configured per directory to generate project-scoped release notes and tags.
  - Path-filtered CI workflows so CLI changes trigger only CLI jobs.
  - Project-specific tags and/or prefixes (e.g., `cli-vX.Y.Z`) with dedicated release pipelines.
  - Separate artifacts and/or dedicated release pages/sections for the CLI.

## Open questions to investigate
- Do we actually have cross-project commits (single commits touching both CLI and OH App)? Confirm by sampling recent history and PR patterns.
- Even with shared history, we can isolate CLI changes via path filters (e.g., `git log -- openhands-cli/`) and monorepo-aware release tooling configured per directory. This would help generate scoped release notes and improve pre-release risk assessment for the CLI.


## Legacy App workflows: investigation plan
- Inventory current workflows in `.github/workflows/` and classify them (App-only, shared, CLI-related). Capture for each:
  - Triggers (on: push/pull_request/tags/schedule) and current path/tag filters
  - Whether they are required checks (branch protection / rulesets), typical duration, and flakiness
- For CLI releases specifically, determine:
  1) Which workflows are currently required to pass in order to release a CLI version (from branch protection and recent release PRs)
  2) Which of those are actually necessary for the CLI (lint, typecheck, unit tests, package build/signing, smoke tests, publish)
  3) How to prevent App workflows from running on CLI-only changes and CLI release PRs:
     - Add path filtering to App workflows so they do not run when only `openhands-cli/**` changes (e.g., `paths-ignore: ["openhands-cli/**"]` or positive `paths:` lists targeting App directories)
     - Add tag filters so App workflows ignore CLI tags (e.g., `tags-ignore: ["cli-v*", "v*-cli"]`)
     - Optionally use a paths-filter job (e.g., `dorny/paths-filter`) and guard jobs with `if:` conditions based on changed areas
     - Consider label-based opt-outs (e.g., a `cli-only` label) as a fallback to skip App pipelines
     - Investigate GitHub Rulesets/branch protection by path to require different checks depending on changed paths

## Testing strategy for agents (fast/dry runs)
- Remotes & safety:
  - Repo has two remotes: origin (fork) and upstream. Agents should push test branches to origin only and open PRs from origin.
  - Use concurrency groups to auto-cancel prior runs for quick iteration.
- Fast CI toggles for CLI workflows:
  - Add `workflow_dispatch` inputs (e.g., `fast: true`) to CLI workflows. When `fast` is true, keep conditions identical but replace heavy steps with quick stubs:
    - Reduce matrix to a single OS (e.g., ubuntu-latest) but this is still too long
    - Replace `pyinstaller` build with `echo` or a minimal `uv build` (no packing)
    - Skip artifact packaging; keep step structure intact
  - Alternatively, gate heavy steps behind `if: inputs.fast != 'true'` and run a placeholder step otherwise
- Path-filter validation workflow:
  - Create a minimal “gate-check” workflow that uses `dorny/paths-filter` and prints which areas changed. This validates path logic without long jobs.
- Heavy App workflows remain real, but should skip on CLI-only changes:
  - Add `paths-ignore: ["openhands-cli/**"]` or positive `paths:` to App workflows so agents can test CLI changes without triggering long builds
- Labels for manual overrides:
  - Define a `cli-only` label to skip App workflows in edge cases where path filters don’t capture intent
- Release testing without waiting hours:
  - Introduce CLI tag patterns for dry runs (e.g., `cli-test-*`) and guard publish steps with an `if:` that runs only for production tag patterns
  - Use `workflow_dispatch` for release workflows with `dry_run: true` to exercise path, artifact, and notes generation logic without publishing



## Branch protection and rulesets: how to fetch (with GH token)
- Use the token from .env (e.g., GITHUB_TOKEN) and query upstream repo protections. Prefer checking upstream (OpenHands/OpenHands), since forks typically have no protections.
- Replace OWNER/REPO accordingly. Example with curl:
  - Branch protection for main:
    ```bash
    curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
      https://api.github.com/repos/OWNER/REPO/branches/main/protection | jq '.'
    ```
  - Repository rulesets:
    ```bash
    curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
      https://api.github.com/repos/OWNER/REPO/rulesets | jq '.'
    ```
- What to capture into this doc:
  - Required status contexts or granular checks for main
  - Any file/path/branch-specific targeting in rulesets that could affect path-filter strategies
- Note: If automation cannot reach api.github.com, run these locally and paste summarized results here.

## Goals and success criteria (acceptance)
- Maintainability first:
  - CLI maintainers can operate and adjust CI/release without touching App tooling (no poetry requirement for CLI-only work)
  - Clear documentation in `openhands-cli/` for local checks (uv) and release steps
- Fast, scoped pipeline for CLI:
  - CLI-only PRs trigger only CLI workflows (path-filtered); App workflows do not run
  - End-to-end CLI CI runtime target: e.g., < 20 minutes from push to artifacts (tune based on actuals)
  - Release tags for CLI trigger only CLI release workflow; App pipelines ignore CLI tags
- Accurate, scoped release output:
  - Release notes include only CLI changes (per-directory tooling like release-please or equivalent)
  - Consistent tag naming for CLI (e.g., `cli-vX.Y.Z` or `vX.Y.Z-cli`) and enforced filters
- No App regressions:
  - App workflows continue to run and protect App changes as before
  - Branch protection / rulesets remain valid; consider conditional required checks by path
- Local DX parity:
  - One command (uv) in `openhands-cli/` runs the same lint/typecheck/tests as CI
  - Pre-commit/Husky hooks are path-aware; CLI-only changes don’t require poetry


## Task brief for implementers (starting points)
- Discover and reuse first:
  - Inventory existing CLI-related workflows under `.github/workflows/` (names containing `cli` or jobs referencing `openhands-cli/`). Prefer adapting these over creating new ones.
  - Map triggers, `paths`/`paths-ignore`, tag filters, and required checks for both App and CLI.
- Tagging and release notes:
  - Propose/confirm a CLI tag pattern (e.g., `cli-vX.Y.Z`). Ensure App workflows ignore these tags.
  - Evaluate monorepo-aware release tooling (e.g., release-please) configured per directory for `openhands-cli/` to scope release notes and versioning.
- Path and condition filters:
  - Add `paths:`/`paths-ignore:` to App workflows so they do not run for changes limited to `openhands-cli/**`.
  - For complex cases, use a `paths-filter` job (e.g., `dorny/paths-filter`) and guard downstream jobs with `if:`.
  - Consider label-based escapes (e.g., `cli-only`) as a manual override.
- Hooks and local DX:
  - Implement the Husky/pre-commit path guard so CLI-only commits don’t require poetry and optionally run `uv`-based checks.
  - Provide simple local commands (`uv run ruff check .`, `uv run pytest -q`, `uv run python build.py`) and document them in `openhands-cli/`.
- Validation plan:
  - Create a PR that changes only files under `openhands-cli/**`. Verify App workflows are skipped and the CLI pipeline runs to completion in the target time budget.
  - Push a test tag matching the CLI pattern to validate that only the CLI release pipeline runs and that artifacts and release notes are scoped to CLI.
  - Confirm branch protection/rulesets still apply appropriately to App changes.
- Rollback plan:
  - Keep changes incremental. If App regressions occur, revert path filters or use tags-ignore to quickly restore previous behavior while iterating.

- Splitting the CLI into its own repository could also provide benefits:
  - Clearer visibility into the challenges of integrating with agent-sdk (surfacing client pain points).
  - Easier tracking and triage of CLI-specific issues independent of the broader project.

## Plan (WIP)
1. Baseline governance  
   - Pull branch protection and ruleset data (per instructions above) to understand which checks are enforced today.  
   - Capture current CLI release path (manual steps, tags in use, time-to-release) to measure improvements.
2. Workflow scoping  
   - Add `paths`/`paths-ignore` guards to heavy App workflows (`py-tests`, `lint`, `ghcr-build`, etc.) so CLI-only diffs trigger just `lint-cli-python`, `test-cli-python`, and `cli-build-binary`.  
   - Use a shared `paths-filter` helper if needed to avoid duplication and enable opt-in overrides via labels.
3. Release stream cleanup  
   - Standardize CLI tag format (`cli-vX.Y.Z` or `vX.Y.Z-cli`) and update `cli-build`/`pypi-release` triggers accordingly.  
   - Introduce scoped release notes (evaluate release-please monorepo config or custom script) that surface only `openhands-cli/**` changes.  
   - Ensure CLI artifacts publish independently of App pipelines (draft release on tag is already in place; confirm publishing UX).
4. Local DX and hooks  
   - Implement Husky path guard + optional uv quick checks so CLI commits no longer require Poetry.  
   - Document the canonical local command set in `openhands-cli/README.md` / `AGENTS.md` (format, lint, test, build).  
   - Evaluate adding a CLI-specific pre-commit config (uv-based) for contributors who want opt-in hooks.
5. Validation + rollout  
   - Create a CLI-only PR to confirm path filters and Husky guard behave as intended; record workflow runtimes.  
   - Dry-run a CLI release tag to ensure only CLI workflows execute and release notes/artifacts look correct.  
   - Communicate the new process to maintainers and update branch protection rules if required checks change.

## Impact (why this matters)
- Slower, harder releases for the CLI (blocked by unrelated CI and flakiness).
- Confusing release history and notes for both users and maintainers.
- Extra maintenance overhead and friction for local development.

This document restates the problems. Next steps: agree on goals for an improved, project-scoped CI/release experience and evaluate options (e.g., monorepo path filters vs dedicated repository) before implementing.

## Appendix: Husky hook repro and mitigation
- Trigger: committing from `openhands-cli/` hits `frontend/.husky/pre-commit`, which assumes App tooling is available.
- Root cause:
  - Hook always runs `npx lint-staged` inside `frontend/`, then executes `poetry run pre-commit` against App/Eval/Test paths.
  - CLI contributors rarely have Poetry environments bootstrapped; the hook fails even though staged files live entirely under `openhands-cli/`.
- Short-term mitigation:
  - Guard the hook by checking `git diff --cached --name-only` for paths outside `openhands-cli/`. Skip frontend + Poetry checks when the diff is CLI-only.
  - Optional: when skipping, run light-weight CLI checks via uv (`uv run ruff check .`, `uv run pytest -q`) if uv is installed.
- Longer-term ideas:
  - Move to a dispatcher script that routes to App/CLI/Enterprise tooling based on path filters.
  - Split pre-commit configs so the CLI uses uv-based hooks, while App/Enterprise continue using Poetry.
