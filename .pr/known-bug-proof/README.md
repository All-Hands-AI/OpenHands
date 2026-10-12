# Known-bug proof: F25.selector-dropdown (#18233) on main vs fix PR #18238

Recipe: the `known-bug F25.selector-dropdown escape-closed` block in
`references/feature-map/F25-backends-and-cloud.md` (recipe hash
`c19f77926f9d31af`), run with this branch's `control-openhands`.

| Side | Revision | Backend | Viewport | Attempts |
|---|---|---|---|---|
| baseline | main `f07aebdf5cdd` | local agent-server 1.54.0, automation 1.19.3 | 1440x1000 | xfail, xfail |
| fix | PR #18238 `77de0ad2486a` | local agent-server 1.54.0, automation 1.19.3 | 1440x1000 | xpass, xpass |

```sh
control-openhands bug run F25.selector-dropdown --attempts 2 --label baseline --run $BASE
control-openhands bug run F25.selector-dropdown --attempts 2 --label fix --run $FIX
control-openhands bug proof F25.selector-dropdown --baseline $BASE --baseline-label baseline --fix $FIX --fix-label fix
```

`proof.json`: `verified`. Every baseline attempt failed at the `# bug` line
(line 11) with value `""`, the value the bug shows; every fix attempt read
`Local`. Doctor passed before and after each failing attempt.

Selector after the two Escapes, baseline (italic placeholder, no status dot)
and fix: `main-escape-closed-1.png`, `main-escape-closed-2.png`,
`pr18238-escape-closed-1.png`, `pr18238-escape-closed-2.png`.

Live negative cases on the baseline run (`baseline-attempts.jsonl`, labels
`negative-*`), none counted as a reproduction:

- `--timeout 1`: `fail`, reason `timeout`.
- Agent server stopped (`service stop agent-server`): `fail`, `setup: doctor
  failed before the attempt`.
- The same with `--no-doctor`: `fail`, `setup: line 3 failed before the
  # bug line`.

Counted together with the two real attempts, they make the baseline
`inconclusive` (`proof-with-negatives.json`: "reproduced the bug in 2 of 5
attempts"); `--baseline-label` sets deliberate negatives aside.

Found while writing the recipe: a reload with the mouse still over the
selector opens its menu and empties the field, which reads like the bug. The
first draft of the recipe did that, and the runner reported it as a setup
failure at the starting-value assertion, not as an `xfail`. The shipped
recipe moves the mouse away first.
