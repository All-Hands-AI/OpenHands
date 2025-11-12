# openhands-cli: CI and Release Pain Points (Problem Statement)

Context: openhands-cli is a self-contained CLI that lives as a subdirectory inside the odie-cli repository. The current CI and release setup is optimized for the broader project, which creates friction for the CLI’s lifecycle.

---

## Executive summary
- **Monorepo friction:** CLI maintainers wait on App/Enterprise pipelines for every release. Noise across Release Notes and GitHub Releases obscures CLI-specific changes.
- **Tooling mismatch:** Shared Husky/Poetry hooks fail on CLI-only commits. Local DX diverges from CI expectations.
- **Workflow scope:** Heavy workflows lack path guards, so CLI PRs trigger app/runtime jobs. Recent updates added filters and a CLI fast-path smoke, but more cleanup remains (release notes, tagging, hooks).


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
- **CLI specific**
  - `cli-build-binary-and-optionally-release.yml`: builds macOS/Linux binaries, drafts releases, now path-scoped (`openhands-cli/**`) and supports a `fast=true` smoke via `workflow_dispatch`.
  - `pypi-release.yml`: publishes App (`release`) on non-CLI tags and CLI (`release-cli`) on tags containing `-cli` or manual dispatch (`reason=cli`).
- **Shared / heavy**
  - `py-tests.yml`: app/enterprise/CLI test matrices (Linux, Windows, enterprise). Recently guarded by `dorny/paths-filter`; CLI jobs remain default-on, others skip when off-path.
  - `lint.yml`: frontend + python linting (root, enterprise, CLI). Path filters now ensure only relevant jobs run for scoped PRs.
  - `ghcr-build.yml`: app/runtime Docker builds. Guards added; only runs when app/runtime/shared paths change or on main/tags.
- **Opt-in / scoped**
  - `e2e-tests.yml`: Playwright, label-gated (`end-to-end`).
  - `fe-unit-tests.yml`: frontend-only (already path-scoped).
  - `enterprise-*`, `ui-*`, `mdx-lint.yml`, `vscode-extension-build.yml`, `dispatch-to-docs.yml`, `lint-fix.yml`, `check-package-versions.yml`, `clean-up.yml`, `stale.yml`: scoped by path, labels, or maintenance triggers.


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

## Current workflow status
### Completed improvements
- Guarded `lint.yml`, `py-tests.yml`, and `ghcr-build.yml` with `dorny/paths-filter`, so CLI-only diffs run just CLI lint/tests/builds while App/Enterprise/Docker jobs report `skipped`.
- Tightened `cli-build-binary-and-optionally-release.yml` push triggers to `openhands-cli/**` and added a `fast=true` smoke mode (`uv run pytest -q` on Linux only).
- Verified CLI tag convention (`1.0.x-cli`) and documented it alongside release workflow behaviour.
- Verification runs:
  - [CLI-only change](https://github.com/enyst/playground/actions/runs/19294526865) — only CLI jobs executed.
  - [Frontend change](https://github.com/enyst/playground/actions/runs/19294624281) — frontend lint/tests triggered, Python/Docker skipped.
  - [Enterprise change](https://github.com/enyst/playground/actions/runs/19294686285) — enterprise lint/tests triggered, other suites skipped.
  - [App validation](https://github.com/enyst/playground/pull/118) — confirmed App paths still execute full pipelines.
  - [CLI fast-path smoke](https://github.com/enyst/playground/actions/runs/19293012005) — macOS matrix skips while Linux entry runs pytest.

### Outstanding workflow actions
- `check-package-versions.yml`: decide whether to skip CLI-only diffs to reduce noise.
- `py-tests.yml`: Windows job remains required for App scopes; consider making it opt-in or removing to match upstream.
- Document fast-path usage in contributor guides (README/AGENTS) so smoke testing is obvious.
- Keep filter lists current as shared directories evolve (e.g., new `scripts/` or generated config folders).

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

- **Release visibility and notes**
  - CLI executables land on the same Releases page as the App, making it hard to identify the latest CLI build.
  - Auto-generated notes blend commits across projects; CLI-specific context gets buried without manual curation.
- **CI coupling and latency**
  - CLI releases wait for every App/Enterprise job, leading to multi-hour lead times and exposure to unrelated flakes.
- **Tooling and local DX**
  - Shared Husky/Poetry hooks fail on CLI-only commits; CLI contributors need uv-based equivalents.
  - Running lint/test/format for just the CLI is harder than it should be because configs live at the repo root.
- **Versioning and tagging**
  - Multiple tag conventions (`X.Y.Z`, `X.Y.Z-cli`) complicate automation and “latest release” discovery.
- **Change risk visibility**
  - Mixed commit history and omnibus release notes make it difficult to reason about CLI-specific risk ahead of releases.

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
- **Workflow hygiene**
  - ✅ Inventory performed above; keep the table current as automation evolves.
  - Add path guards to remaining low-cost workflows (`check-package-versions`, docs) or explicitly document why they must run.
- **Release process**
  - Standardize CLI tag enforcement (suffix `-cli` or introduce prefix) and ensure App workflows ignore the pattern.
  - Introduce per-directory release notes (release-please manifests or custom script) so GitHub Releases stay scoped.
- **Local developer experience**
  - Implement Husky guard to skip Poetry when staged paths are under `openhands-cli/`; optionally run `uv` lint/tests when available.
  - Publish a CLI-specific pre-commit config for opt-in checks mirroring CI (`uv run ruff check .`, `uv run pytest`, etc.).
- **Validation**
  - Schedule periodic smoke PRs (CLI-only, Frontend, Enterprise, App) to confirm filters continue to behave; record durations for regressions.
  - Dry-run a CLI release tag to validate GitHub Release + PyPI flows after changes to tagging or automation.
- **Architecture follow-ups**
  - Evaluate benefits of splitting CLI into its own repo once CI noise is minimized (improved release cadence, independent issue triage).

## Plan (WIP)
1. **Governance & visibility**
   - Pull branch protection / required check data with maintainer credentials and document it.
   - Automate CLI release notes so GitHub Releases highlight only `openhands-cli/**` commits.
2. **Workflow hardening**
   - Finish scoping low-cost workflows and reconfirm Docker behaviour on CLI tags.
   - Decide the fate of the Windows job (optional dispatch or removal) to reduce queue contention.
3. **Release stream cleanup**
   - Enforce consistent CLI tag naming (lint in CI or tooling support).
   - Add automation to copy CLI-specific notes into the GitHub Release draft generated by the binary workflow.
4. **Local DX**
   - Ship the Husky guard + optional `uv` quick checks; advertise in README/AGENTS.
   - Offer a CLI-specific pre-commit configuration for contributors wanting automatic lint/test.
5. **Validation & rollout**
   - Maintain a schedule of smoke PRs (CLI/Frontend/Enterprise/App) after major changes; track runtimes for regressions.
   - Socialize new processes with maintainers and adjust branch protection rules if check names change.

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
