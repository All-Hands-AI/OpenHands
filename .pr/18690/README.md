# Issue #18690 verification

Captured from the real local Agent Canvas stack on macOS arm64. Agent Server
1.56.0 and automation 1.22.0 were used before and after the change. The baseline
was OpenHands/OpenHands commit 8d39305538c1d17a30cbe477e57a0e18fcee7d95.
The local executable plugin is a verification fixture, not a mocked API response.
All automations were disabled. No run was dispatched and no LLM was called.

## Reproduction

1. Use Node 24 and install the committed dependency lock with `npm ci --ignore-scripts`.
2. Launch the repository's `control-openhands` CLI with `launch --new`, then run
   `doctor` and `onboard --skip` against that isolated run.
3. Create a local plugin with `.plugin/plugin.json` containing a name, version,
   description and an `automation` object: schema version
   `openhands.automation.plugin.v1`, script entrypoint `python3 worker.py`,
   working directory `scripts`, and an object config schema.
4. Create the inactive automation using `api POST /api/automation/v1/plugin-spec
   --write --data @<request.json>`. The request supplies the local plugin source,
   an event trigger, timeout 300, and config containing a long instruction,
   `dry_run: false`, `retry_count: 0`, and `routing: {queue: "reviews"}`.
5. Open `/automations/<response-id>` through `browser goto`.
6. On the baseline the entrypoint is followed by the generic unavailable-tarball
   message and the plugin config/timeout are missing (`before.png`).
7. On this branch the runtime explanation, source, config and timeout are visible
   (`after.png`). Show more/less reveals and collapses the complete instruction
   (`expand-collapse.gif`). Phone width was 390 px (`phone.png`), with no
   document-width overflow.
8. A second real request with an empty config and optional `ref`/`repo_path`
   verified that source metadata renders without an empty config block
   (`empty-config.png`). A local source does not check out the supplied ref;
   this check concerns the response's source metadata presentation.

## Additional checks

- A real uploaded tarball still lists `main.py` and its `print("pong")` contents.
- A real prompt preset still renders its prompt. The existing Export, Tarball,
  Edit, Turn on/off and Delete actions remain present.
- Plugin detail navigation requests the existing detail and runs endpoints;
  no tarball or plugin-definition fetch is made. No app/page errors observed.
- The six added regressions failed against the baseline; the related suite then
  passed all 36 tests after the fix.
- `npm test`: 845 files passed, 9250 tests passed, 7 existing todo.
- `npm run lint`, `npm run build`, `npm run build:lib`, and
  `npm run check-translation-completeness` passed.
- Full tests used Node 24.22.0 and Python 3.13 with native process permissions.
  An initial sandboxed run hit unrelated Python 3.9 and launcher-permission
  failures; the complete native run passed. Test-created user state was cleaned.
