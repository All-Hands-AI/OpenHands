# Known-bug runner: before and after

Both runs drive real `bug run` attempts through bash and the CLI against an
offline run directory (`--no-doctor`), with the recipe's marked command
`control-openhands assert --field count --equals 1 --bug-shows 0 -- evidence list --feature QA  # bug`
(an empty ledger prints `count: 0`, the "bug").

| Recipe | main (d7e14e2) | this branch |
| --- | --- | --- |
| Marked assert continued over three lines with `\` | `map check` rejects it: "the `# bug` line must be a `control-openhands assert`" (it reads only the last line) | `xfail`, failing line 2 = the command's first line |
| `trap '... assert ...; false' EXIT` cleanup after the marked command fails | `fail`: "setup: line -2 failed before the `# bug` line" (the trap's `false` overwrote the recorded failure) | `xfail` at line 3: the first failure is kept, and the trap's assertions are tagged `after-failure` |
| `--bug 'count eq 0'` | (flag ignored) | `xfail` |
| `--bug 'count eq 0 && count ne 0'` | `xfail` (flag ignored, any mismatch counted) | `fail`: wrong symptom |

`npx vitest run .agents/skills/verify-openhands`: 61 passed.
`control-openhands map check`: ok, 27 files, 747 IDs; `bug list`: F25.selector-dropdown well formed.
