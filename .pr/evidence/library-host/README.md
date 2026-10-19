I am an AI agent helping Engel Nyst (@enyst) with project work.

# Normal library host proof

Build the selected package with `npm run build:lib`. The supplied host imports `@openhands/agent-canvas` by package name and mounts a button inside AgentServerUIRoot. In host/, install the exact listed dependencies (the package uses file:../../../..) and run `npx vite --host 127.0.0.1 --port PORT`. No import alias or global require shim is supplied. This run reused owned links to the existing exact-pinned modules instead of reinstalling them. The HTML error element only observes native window errors.

Write the host loopback URL to the owned control-openhands run workspace/library-host-url. Use `control-openhands bug run F26.lib-host-app --file .pr/evidence/library-host/recipe.md --attempts 2 --label LABEL --run RUN` on base and fix, then compare using `control-openhands bug proof F26.lib-host-app --file .pr/evidence/library-host/recipe.md --baseline BASE_RUN --fix FIX_RUN --baseline-label baseline-host --fix-label fix-host-final`.

paired-proof.json records two baseline xfails and two fixed xpasses with the identical recipe and backend/viewport. The fixed recording includes a real button click from 0 to 1. The build test separately runs native ESM and CJS consumers and checks React/Motion identity with the host dependencies.

A preliminary React-only fix exposed Motion's optional peer require being hoisted outside its guarded try/catch. That candidate was not counted as fixed. The final product commit also externalizes the existing framer-motion dependency. Only the final verified comparison is published here. Both external hosts and the fixed Canvas run were stopped; shared dependency data was preserved.
