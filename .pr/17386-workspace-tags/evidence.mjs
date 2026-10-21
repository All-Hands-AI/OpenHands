#!/usr/bin/env node
/**
 * Headless running-Canvas evidence for #17386 (workspace grouping persisted
 * via the server-side `workspace` conversation tag). No agent-server or LLM:
 * the frontend runs against its MSW mock API.
 *
 * Usage (from the repo root):
 *   VITE_MOCK_API=true npx react-router dev --port 5199 --strictPort
 *   node .pr/17386-workspace-tags/evidence.mjs --label after    # this branch
 *   node .pr/17386-workspace-tags/evidence.mjs --label before   # main's src/
 *
 * Scenario (identical for both labels):
 *   - local backend selected, sidebar in "grouped" mode
 *   - workspace `/workspace/project` registered on the (mock) agent-server
 *   - conversation "My New Project" carries the server tag
 *     `workspace=/workspace/project`; the three `/workspace/project`
 *     fixtures are legacy local_repo conversations with no tag
 *   - `openhands-agent-server-conversation-metadata` is empty, i.e. another
 *     browser / device / cleared site data
 * main groups everything under "No workspace"; the branch regroups the tagged
 * conversation via the tag and the legacy ones via their working_dir.
 */
import { chromium } from "../../node_modules/playwright/index.mjs";

const argv = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};
const label = arg("label", "after");
const base = arg("url", "http://localhost:5199");
const outDir = arg("out", new URL(".", import.meta.url).pathname);

const WORKSPACE = {
  id: "project",
  name: "project",
  path: "/workspace/project",
};

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});

await context.addInitScript(() => {
  const backend = {
    id: "local-1",
    name: "Local agent-server",
    host: location.origin,
    apiKey: "mock-key",
    kind: "local",
  };
  localStorage.setItem("openhands-onboarded", "1");
  localStorage.setItem(
    "openhands-sidebar-onboarding-checklist-dismissed",
    "true",
  );
  localStorage.setItem("openhands-backends", JSON.stringify([backend]));
  // Grouped sidebar: the mode that shows workspace folders.
  localStorage.setItem(
    "conversation-panel-preferences",
    JSON.stringify({ state: { organizeMode: "grouped" }, version: 0 }),
  );
  const selection = JSON.stringify({ backendId: backend.id, orgId: null });
  localStorage.setItem("openhands-active-backend", selection);
  sessionStorage.setItem("openhands-active-backend", selection);
  // The state under test: no client-side conversation metadata cache.
  localStorage.removeItem("openhands-agent-server-conversation-metadata");
  // The mock API has no event socket; keep the client from retrying.
  class NeverOpenSocket {
    constructor() {
      this.readyState = 0;
    }
    send() {}
    close() {}
    addEventListener() {}
    removeEventListener() {}
  }
  window.WebSocket = NeverOpenSocket;
});

const page = await context.newPage();
await page.goto(`${base}/`, { waitUntil: "domcontentloaded" });
await page.waitForSelector('[data-testid="conversation-panel"]', {
  timeout: 60_000,
});
// The analytics consent dialog opens once the backend settings resolve.
const confirm = page.getByRole("button", { name: "Confirm preferences" });
await confirm.waitFor({ state: "visible", timeout: 15_000 }).catch(() => {});
if (await confirm.isVisible().catch(() => false)) {
  await confirm.click();
  await confirm.waitFor({ state: "hidden", timeout: 10_000 }).catch(() => {});
}

await page.evaluate(async (workspace) => {
  const json = { "content-type": "application/json" };
  await fetch("/api/workspaces", {
    method: "POST",
    headers: json,
    body: JSON.stringify({ workspaces: [workspace] }),
  });
  await fetch("/api/conversations/1", {
    method: "PATCH",
    headers: json,
    body: JSON.stringify({ tags: { workspace: workspace.path } }),
  });
  const prefs =
    await import("/src/stores/conversation-panel-preferences-store.ts");
  prefs.useConversationPanelPreferencesStore
    .getState()
    .setOrganizeMode("grouped");
  const { queryClient } = await import("/src/query-client-config.ts");
  await queryClient.invalidateQueries();
}, WORKSPACE);

// Conversation rows always render; folders only exist in grouped mode when
// there is more than one group, so wait for rows and give folders a moment.
await page.waitForSelector('a[href^="/conversations/"]', { timeout: 30_000 });
await page
  .waitForSelector('[data-testid^="thread-folder-"]', { timeout: 45_000 })
  .catch(() => {});
await page.waitForTimeout(2_000);
const organizeMode = await page.evaluate(async () => {
  const prefs =
    await import("/src/stores/conversation-panel-preferences-store.ts");
  return prefs.useConversationPanelPreferencesStore.getState().organizeMode;
});
console.log(JSON.stringify({ label, organizeMode }));

const folders = await page.$$eval('[data-testid^="thread-folder-"]', (els) =>
  els
    .filter((el) => el.tagName === "SECTION")
    .map((el) => ({
      id: el.getAttribute("data-testid"),
      title: el
        .querySelector("h2, h3, [id^='thread-folder-']")
        ?.textContent?.trim(),
      conversations: el.querySelectorAll('a[href^="/conversations/"]').length,
    })),
);
console.log(JSON.stringify({ label, folders }, null, 2));

await page.screenshot({ path: `${outDir}/${label}-full.png` });
await page.screenshot({
  path: `${outDir}/${label}-sidebar.png`,
  clip: { x: 0, y: 0, width: 360, height: 900 },
});
await browser.close();
