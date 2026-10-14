# #17953 before/after on a live Canvas stack

Both runs: `control-openhands launch --new --build always`, `onboard --skip`, Agent Server 1.54.0,
headless Chromium 1440x1000. "main" is `0e9ce19` with this PR's `src/` changes stashed; "fix" is this branch.
Script steps per bug follow the issue's Steps to Reproduce.

| Check | main | fix |
|---|---|---|
| 1. Escape in Edit backend: `count edit-backend-modal` / `count manage-backends-modal` | 0 / 0 | 1 / 1 |
| 1. Host Name after Escape | modal gone | `QA Draft` |
| 2. `/shared/conversations/<missing id>`: toast history | 1 toast, "Not Found" | empty |
| 3. Cloud login to `http://127.0.0.1:9`: open tabs before / after failure / after Try again | 1 / 2 / 3 (extra tabs `about:blank`) | 1 / 1 / 1 |
