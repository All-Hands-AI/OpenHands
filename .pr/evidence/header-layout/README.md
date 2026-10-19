I am an AI agent helping Engel Nyst (@enyst) with project work.

# Phone automation header proof

The same live F23.phone/detail-header-clipping recipe reproduces clipping twice on base and passes twice on the fix. The fixed product revision is in summary.json. No verification-skill files were modified.

With the repository dependencies installed, use control-openhands launch from the selected checkout and its supported backend pins, then doctor/onboard. Run `control-openhands bug run F23.phone --name detail-header-clipping --attempts 2 --label LABEL --run RUN` using the maintained feature recipe, then `control-openhands bug proof F23.phone --baseline BASE_RUN --fix FIX_RUN --baseline-label baseline --fix-label fix`. Labels must match the attempts being compared; the saved paired proof is authoritative for this run.

The durable real-backend regression is `tests/e2e/mock-llm/automations/mock-llm-automation-header.spec.ts` via `playwright.mock-llm.config.ts`. It creates an inert disabled event automation, sets actual language preferences, checks document direction, measures every header control, clicks the switch on/off at 390 and 1440 pixels, and deletes the fixture. It needs the normal full test stack/session configuration, but makes no LLM request.

geometry.json is additional CLI readback for Arabic/English at phone/desktop widths plus a short-name phone control. All five cases fit; four switch cycles were driven through pointer clicks. Before/after images are real Chromium screenshots. No screenshot was edited.
