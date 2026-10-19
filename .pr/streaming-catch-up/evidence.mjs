// Reviewer artifact: streams a markdown reply into the running Canvas through
// the real event store at a realistic model speed, and records how long the
// chat keeps typing after the model has finished.
//
//   VITE_MOCK_API=true npx react-router dev --port 5199 --strictPort
//   node .pr/streaming-catch-up/evidence.mjs <label> <outDir> [baseUrl]
//
// Writes <label>-model-done-plus-<n>s.png, <label>-fully-shown.png,
// <label>-summary.json and <label>.webm into <outDir>.
import { mkdirSync, renameSync, writeFileSync, readdirSync } from "node:fs";
import { chromium } from "playwright";

const [, , label, outDir, baseUrl = "http://localhost:5199"] = process.argv;
if (!label || !outDir) {
  console.error("usage: node evidence.mjs <label> <outDir> [baseUrl]");
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

// ~2000 characters of markdown-heavy reply, the kind of answer the report was
// about (headings, lists, a table, code).
const REPLY = `## Python packaging in 2026: a short guide

Modern Python packaging has settled on a few conventions. This guide walks through the pieces you actually need: a \`pyproject.toml\`, a build backend, a lock file, and a release workflow.

### 1. Project layout

Use the **src layout**. It keeps tests from importing the working copy by accident and makes the installed package the only thing on the path:

\`\`\`text
my-package/
  pyproject.toml
  README.md
  src/
    my_package/
      __init__.py
      core.py
  tests/
    test_core.py
\`\`\`

### 2. The manifest

Everything lives in \`pyproject.toml\`. The \`[project]\` table is standardised (PEP 621), so it works with every backend:

\`\`\`toml
[project]
name = "my-package"
version = "0.3.0"
description = "A small example"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "pydantic>=2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
\`\`\`

### 3. Choosing a build backend

| Backend | Best for | Notes |
|---|---|---|
| hatchling | Pure-Python projects | Sensible defaults, plugin system |
| setuptools | Legacy projects, C extensions | Needs \`setup.py\` only for extensions |
| maturin | Rust extensions | Builds wheels with PyO3 |
| flit-core | Tiny libraries | Minimal configuration |

For most libraries, **hatchling** is the pragmatic choice.

### 4. Locking and environments

- Use \`uv\` for day-to-day work: \`uv sync\` creates the environment and writes \`uv.lock\`.
- Commit the lock file for applications; do *not* commit it for libraries.
- Pin tool versions in \`[dependency-groups]\` so CI and laptops agree.

### 5. Releasing

1. Bump the version in \`pyproject.toml\` (or let \`hatch version\` do it).
2. Build: \`uv build\` produces an sdist and a wheel in \`dist/\`.
3. Publish with trusted publishing from GitHub Actions, which needs no API token.
4. Tag the commit and write release notes.

> **Tip:** run \`python -m twine check dist/*\` before publishing to catch a broken README render.

That is the whole workflow. Everything else, from entry points to optional extras, is a small addition to the same file.`;

const MODEL_CPS = 300; // characters per second the model delivers
const CHUNK = 30; // characters per chunk (one chunk every 100 ms)

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 800 },
  recordVideo: { dir: `${outDir}/raw-video-${label}`, size: { width: 1280, height: 800 } },
});
const page = await context.newPage();

await page.addInitScript(() => {
  // Skip first-run onboarding and register the mock server as a local backend
  // so the conversation page renders.
  try {
    localStorage.setItem("openhands-onboarded", "1");
    const backend = { id: "evidence-local", name: "Local", host: location.origin, apiKey: "mock-key", kind: "local" };
    localStorage.setItem("openhands-backends", JSON.stringify([backend]));
    const selection = JSON.stringify({ backendId: backend.id, orgId: null });
    localStorage.setItem("openhands-active-backend", selection);
    sessionStorage.setItem("openhands-active-backend", selection);
  } catch {}
  // Keep the page's event sockets from ever connecting: a socket that stays
  // CONNECTING never triggers the "clear streaming slots" paths.
  class NeverConnecting extends EventTarget {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;
    constructor(url) {
      super();
      this.url = String(url);
      this.readyState = 0;
      this.binaryType = "blob";
    }
    send() {}
    close() {
      this.readyState = 3;
    }
  }
  window.WebSocket = NeverConnecting;
});

page.on("pageerror", (err) => console.error("[pageerror]", err.message));

await page.goto(`${baseUrl}/conversations/1`, { waitUntil: "networkidle", timeout: 120000 });
await page.waitForSelector('[data-testid="chat-interface"]', { timeout: 60000 });
await page.waitForTimeout(1500);
// Dismiss the analytics consent modal if it is up.
const confirm = page.getByRole("button", { name: "Confirm preferences" });
if (await confirm.isVisible().catch(() => false)) {
  await confirm.click();
  await page.waitForTimeout(500);
}

// Start the stream inside the page and expose progress on window.__evidence.
await page.evaluate(
  async ({ reply, cps, chunk }) => {
    const mod = await import("/src/stores/use-event-store.ts");
    const store = mod.useEventStore;
    const itemId = `evidence-${Date.now()}`;
    const t0 = performance.now();
    const state = { modelDoneAt: null, shownAt: null, samples: [] };
    window.__evidence = state;

    const overlay = document.createElement("div");
    overlay.style.cssText =
      "position:fixed;top:8px;right:8px;z-index:99999;background:#111;color:#fff;font:14px/1.4 monospace;padding:8px 10px;border-radius:6px;opacity:0.92;white-space:pre";
    document.body.appendChild(overlay);

    const lastBubble = () => {
      const bubbles = document.querySelectorAll('[data-testid="agent-message"]');
      return bubbles[bubbles.length - 1] ?? null;
    };
    const tick = () => {
      const now = performance.now() - t0;
      const bubble = lastBubble();
      const shown = bubble ? (bubble.textContent ?? "").length : 0;
      // Words still fading in mark a reply that is still being revealed.
      const stillTyping = bubble ? bubble.querySelector("[data-stream-word]") !== null : true;
      if (state.modelDoneAt !== null && state.shownAt === null && !stillTyping) {
        state.shownAt = now;
      }
      state.samples.push({ t: Math.round(now), shown });
      const modelLine =
        state.modelDoneAt === null
          ? `model: streaming at ${cps} chars/s`
          : `model: finished at ${(state.modelDoneAt / 1000).toFixed(1)}s`;
      const shownLine =
        state.shownAt === null
          ? `chat: still typing (${shown} chars shown)`
          : `chat: fully shown at ${(state.shownAt / 1000).toFixed(1)}s`;
      overlay.textContent = `t = ${(now / 1000).toFixed(1)}s\n${modelLine}\n${shownLine}`;
    };
    setInterval(tick, 100);

    store.getState().openStreamingSlot({ type: "item_started", item_id: itemId, attempt: 1, anchor_seq: null });
    let order = 0;
    let sent = 0;
    const timer = setInterval(() => {
      const piece = reply.slice(sent, sent + chunk);
      sent += piece.length;
      store.getState().appendStreamingDeltas([
        { type: "delta", item_id: itemId, attempt: 1, order: order++, kind: "text", content: piece },
      ]);
      if (sent >= reply.length) {
        clearInterval(timer);
        state.modelDoneAt = performance.now() - t0;
        // The durable message replaces the slot in place, as the server's does.
        store.getState().addEvent({
          id: itemId,
          timestamp: new Date().toISOString(),
          source: "agent",
          llm_message: { role: "assistant", content: [{ type: "text", text: reply }] },
          activated_skills: [],
          extended_content: [],
        });
      }
    }, (chunk / cps) * 1000);
  },
  { reply: REPLY, cps: MODEL_CPS, chunk: CHUNK },
);

// Screenshots at fixed offsets after the model finished, until fully shown.
const offsets = [0, 3, 10, 20, 30];
const taken = new Set();
let status = null;
const started = Date.now();
while (Date.now() - started < 90000) {
  status = await page.evaluate(() => {
    const s = window.__evidence;
    return { modelDoneAt: s.modelDoneAt, shownAt: s.shownAt, last: s.samples[s.samples.length - 1] };
  });
  if (status.modelDoneAt !== null) {
    const since = (status.last.t - status.modelDoneAt) / 1000;
    for (const offset of offsets) {
      if (!taken.has(offset) && since >= offset) {
        taken.add(offset);
        await page.screenshot({ path: `${outDir}/${label}-model-done-plus-${offset}s.png` });
      }
    }
    if (status.shownAt !== null) {
      await page.waitForTimeout(500);
      await page.screenshot({ path: `${outDir}/${label}-fully-shown.png` });
      break;
    }
  }
  await page.waitForTimeout(200);
}

const samples = await page.evaluate(() => window.__evidence.samples);
const summary = {
  label,
  replyChars: REPLY.length,
  modelCps: MODEL_CPS,
  modelDoneS: status.modelDoneAt / 1000,
  fullyShownS: status.shownAt === null ? null : status.shownAt / 1000,
  typingAfterModelDoneS: status.shownAt === null ? null : (status.shownAt - status.modelDoneAt) / 1000,
};
writeFileSync(`${outDir}/${label}-summary.json`, JSON.stringify({ ...summary, samples }, null, 2));
console.log(JSON.stringify(summary));

await page.waitForTimeout(1000);
await context.close();
await browser.close();
const [video] = readdirSync(`${outDir}/raw-video-${label}`);
if (video) renameSync(`${outDir}/raw-video-${label}/${video}`, `${outDir}/${label}.webm`);
