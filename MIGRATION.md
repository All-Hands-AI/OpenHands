# Poetry usage audit

This document catalogs all usages of Poetry across the repository and provides a reproducible command to regenerate the report.

## How to regenerate this report

Run the following command from the repository root to (re)generate MIGRATION.md with current findings:

```bash
bash -lc '{ echo "# Poetry usage audit"; echo; echo "Generated on $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo; echo "## Indicators of Poetry usage (files)"; git ls-files -z | tr "\0" "\n" | grep -E "(^|/)poetry\.lock$|(^|/)pyproject\.toml$" | sed "s/^/- /" || true; echo; echo "## Lines mentioning '\''poetry'\'' (code, scripts, config)"; git grep -nI --heading -E "(^|[^A-Za-z])poetry([^A-Za-z]|$)" || true; echo; echo "## [tool.poetry] sections in pyproject.toml"; if git grep -q --no-color "\[tool\.poetry\]" -- "pyproject.toml"; then git grep -n --no-color "\[tool\.poetry\]" -- "pyproject.toml"; echo; git grep -n -A5 -B1 "\[tool\.poetry\]" -- "pyproject.toml"; else echo "No [tool.poetry] sections found."; fi; echo; echo "## CI/CD workflow references (.github/workflows)"; git grep -nI -E "(^|[^A-Za-z])poetry([^A-Za-z]|$)|pipx install poetry" -- ".github/workflows" || true; echo; echo "## Dockerfile references"; git grep -nI -E "(^|[^A-Za-z])poetry([^A-Za-z]|$)|pipx install poetry" -- "*Dockerfile*" "docker" "containers" 2>/dev/null || true; echo; echo "## Makefile references"; git grep -nI -E "(^|[^A-Za-z])poetry([^A-Za-z]|$)|poetry\s+run|poetry\s+install" -- "Makefile" || true; echo; echo "## Shell scripts referencing poetry (*.sh)"; if git ls-files "*.sh" >/dev/null 2>&1; then git ls-files "*.sh" -z | xargs -0 grep -nIH -E "(^|[^A-Za-z])poetry([^A-Za-z]|$)" || true; else echo "No shell scripts found."; fi; } > MIGRATION.md'
```

Notes:
- The search is case-sensitive and avoids binary files.
- Update the patterns in the sections above if you keep Poetry under unconventional paths.

## Current findings

Run the command above to populate this section with an up-to-date audit.
