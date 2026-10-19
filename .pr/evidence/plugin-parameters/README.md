I am an AI agent helping Engel Nyst (@enyst) with project work.

# Unsupported Local plugin parameters

The issue accepts honoring a supported runtime contract or clearly rejecting an unsupported configuration before creation. Agent Server PluginSource does not have a parameters field in the supported floor or tested release; schema-boundary.json records exact source links and the observed runtime OpenAPI field names. This fix chooses explicit rejection. It does not add an unsupported field or claim runtime parameter delivery.

The existing maintained F19.launch-parameters/local-delivery recipe is unchanged and reproduced the original actual-201/silently-dropped-fields defect twice on base. It is not reclassified as an xpass. unsupported-recipe.md separately proves the documented rejection alternative twice on each revision. phone-recipe.md repeats it at 390x844.

Use `control-openhands bug run F19.launch-parameters --file RECIPE --name unsupported-local --attempts 2 --label LABEL --run RUN` with the same recipe on base and fix; then `control-openhands bug proof F19.launch-parameters --file RECIPE --baseline BASE_RUN --fix FIX_RUN --baseline-label BASE_LABEL --fix-label FIX_LABEL`. Saved verdicts include recipe hashes.

For the real positive control, activate the checked-in CLI, export OH_VERIFY_RUN to an owned fixed run with a configured profile, and run `python .pr/evidence/plugin-parameters/positive-control.py`. It supplies no message, creates an inert plugin, drives trust and Start, verifies the actual 201 request coordinates and conversation navigation, deletes its conversations, and removes the fixture. No model response is requested.

The screenshots/video are genuine Chromium captures. Private raw request bodies, credentials, profiles and session files are excluded. The fixed run was stopped and private state purged after the controls.
