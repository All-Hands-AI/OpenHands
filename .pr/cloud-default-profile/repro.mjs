// usage: QA_MODE=before|after [QA_DRYRUN=1] [QA_STEPS=s1,s2,s3] node .tmp/qa-cloud/repro.mjs
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { chromium } from "playwright";

const FRONT = process.env.QA_FRONT ?? "http://127.0.0.1:18711";
const HOST = "https://app.shared-8.replicated.all-hands-testing.dev";
const KEY = readFileSync(`${process.env.HOME}/.oh-fleet-shared8-key`, "utf8").trim();
const ORG = "b6f2a99b-68fa-40fa-b28b-07f38ca733e3";
const MODE = process.env.QA_MODE ?? "before";
const DRY = !!process.env.QA_DRYRUN;
const STEPS = (process.env.QA_STEPS ?? "s1,s2,s3").split(",");
const OUT = `${process.env.QA_OUT ?? ".tmp/qa-cloud/out"}/${MODE}${DRY ? "-dry" : ""}`;
mkdirSync(OUT, { recursive: true });

async function api(method, path, body) {
  const res = await fetch(`${HOST}${path}`, {
    method,
    headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json = text;
  try {
    json = JSON.parse(text);
  } catch {}
  return { status: res.status, body: json };
}
const agentProfile = async (name) => (await api("GET", `/api/agent-profiles/${name}`)).body.profile;
const agentProfiles = async () => (await api("GET", "/api/agent-profiles")).body;
const orgActiveLlm = async () => (await api("GET", `/api/organizations/${ORG}/profiles`)).body.active_profile;
const activateAgent = async (name) => {
  const { profiles } = await agentProfiles();
  return api("POST", `/api/agent-profiles/${profiles.find((p) => p.name === name).id}/activate`, {});
};

async function reset(active) {
  await api("POST", "/api/agent-profiles/default", { agent_kind: "openhands", llm_profile_ref: "qa-alpha", mcp_server_refs: [], secret_refs: [] });
  await api("POST", "/api/agent-profiles/qa-reviewer", { agent_kind: "openhands", llm_profile_ref: "qa-alpha" });
  await api("POST", `/api/organizations/${ORG}/profiles/qa-beta/activate`, {});
  await activateAgent(active);
}

const results = [];
function record(name, info) {
  results.push({ name, ...info });
  console.log(`${name}: ${JSON.stringify(info)}`);
}

const requests = [];
const starts = [];
const blocked = [];
async function intercept(context) {
  await context.route("**/*", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    if (url.origin === HOST) requests.push(`${req.method()} ${url.pathname}`);
    if (req.method() !== "POST" || url.origin !== HOST) return route.continue();
    let body = {};
    try {
      body = req.postDataJSON() ?? {};
    } catch {}
    if (/^\/api\/v1\/app-conversations\/?$/.test(url.pathname)) {
      const entry = { agent_profile_id: body.agent_profile_id ?? null, llm_model: body.llm_model ?? null, had_message: !!body.initial_message };
      starts.push(entry);
      if (DRY) {
        entry.response = { status: 503, dryRun: true };
        return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "QA dry run" }) });
      }
      const response = await route.fetch({ postData: JSON.stringify({ ...body, initial_message: null }) });
      let json = null;
      try {
        json = await response.json();
      } catch {}
      entry.response = { status: response.status(), id: json?.id ?? null };
      return route.fulfill({ response });
    }
    if (/(\/events|\/messages|pending-messages|\/run|\/ask_agent|\/generate_title)\/?$/.test(url.pathname)) {
      blocked.push(url.pathname);
      return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "blocked by QA: no model calls" }) });
    }
    return route.continue();
  });
}

async function waitStart(taskId, timeoutS = 300) {
  for (let i = 0; i < timeoutS / 5; i++) {
    const t = (await api("GET", `/api/v1/app-conversations/start-tasks?ids=${taskId}`)).body?.[0];
    if (t && (t.status === "READY" || t.status === "ERROR")) return t;
    await new Promise((r) => setTimeout(r, 5000));
  }
  return null;
}
async function pauseSandbox(conversationId) {
  const sandbox = (await api("GET", `/api/v1/app-conversations?ids=${conversationId}`)).body?.[0]?.sandbox_id;
  if (sandbox) await api("POST", `/api/v1/sandboxes/${sandbox}/pause`);
  return sandbox ?? null;
}

async function gotoHome(page) {
  await page.goto(`${FRONT}/`, { waitUntil: "domcontentloaded" });
  await page.getByTestId("home-chat-launcher").waitFor({ timeout: 60_000 });
  await page.getByTestId("chat-input-llm-profile").waitFor({ timeout: 60_000 });
  await page.waitForTimeout(3000);
}
const pills = async (page) => ({
  agent: (await page.getByTestId("chat-input-agent-profile").count()) ? (await page.getByTestId("chat-input-agent-profile").innerText()).trim() : null,
  llm: await page.getByTestId("chat-input-llm-profile").getAttribute("title"),
});
async function pickLlm(page, name, shot) {
  await page.getByTestId("chat-input-llm-profile").click();
  await page.getByTestId(`chat-input-llm-profile-option-${name}`).waitFor({ timeout: 15_000 });
  await page.screenshot({ path: `${OUT}/${shot}` });
  await page.getByTestId(`chat-input-llm-profile-option-${name}`).click();
  await page.waitForTimeout(4000);
}
async function launchFromHome(page) {
  const n = starts.length;
  await page.getByTestId("chat-input").waitFor({ state: "visible", timeout: 60_000 });
  await page.evaluate(() => {
    const el = document.querySelector('[data-testid="chat-input"]');
    el.focus();
    el.textContent = "QA cloud repro launch";
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: "QA cloud repro launch", inputType: "insertText" }));
  });
  await page.getByTestId("submit-button").click();
  for (let i = 0; i < 60 && !starts[n]?.response; i++) await page.waitForTimeout(500);
  return starts[n] ?? null;
}

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 860 } });
await context.addInitScript(() => {
  window.localStorage.setItem("analytics-consent", "false");
  window.localStorage.setItem("openhands-telemetry-consent", "denied");
  window.localStorage.setItem("openhands-telemetry-first-use", "true");
  window.localStorage.setItem("openhands-onboarded", "1");
});
await intercept(context);
const page = await context.newPage();
const consoleErrors = [];
page.on("console", (m) => {
  if (m.type() === "error") consoleErrors.push(m.text().slice(0, 300));
});

try {
  await page.goto(`${FRONT}/`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.evaluate(
    ({ HOST, KEY, ORG }) => {
      const backends = JSON.parse(window.localStorage.getItem("openhands-backends") || "[]").filter((b) => b.id !== "qa-cloud");
      backends.push({ id: "qa-cloud", name: "shared-8", host: HOST, apiKey: KEY, kind: "cloud" });
      window.localStorage.setItem("openhands-backends", JSON.stringify(backends));
      window.localStorage.setItem("openhands-active-backend", JSON.stringify({ backendId: "qa-cloud", orgId: ORG }));
      window.sessionStorage.removeItem("openhands-active-backend");
    },
    { HOST, KEY, ORG },
  );

  if (STEPS.includes("s1")) {
    // `default` is active with its own LLM qa-alpha; the org's active LLM is qa-beta.
    await reset("default");
    await gotoHome(page);
    const shown = await pills(page);
    await page.screenshot({ path: `${OUT}/s1-home.png` });
    await pickLlm(page, "qa-gamma", "s1-menu.png");
    const afterPick = await pills(page);
    await page.screenshot({ path: `${OUT}/s1-after-pick.png` });
    const state = { defaultRef: (await agentProfile("default")).llm_profile_ref, orgActive: await orgActiveLlm() };
    const start = await launchFromHome(page);
    let ran = null;
    if (start?.response?.id) {
      const task = await waitStart(start.response.id);
      const conv = task?.app_conversation_id ? (await api("GET", `/api/v1/app-conversations?ids=${task.app_conversation_id}`)).body?.[0] : null;
      ran = { status: task?.status ?? "timeout", detail: task?.detail ?? null, llm_model: conv?.llm_model ?? null, launched: conv?.launched_agent_profile ?? null };
      if (task?.app_conversation_id) ran.pausedSandbox = await pauseSandbox(task.app_conversation_id);
    }
    record("s1 default on home", { shown, afterPick, state, start, ran });
  }

  if (STEPS.includes("s2")) {
    // A named profile is active with qa-alpha.
    await reset("qa-reviewer");
    await gotoHome(page);
    const shown = await pills(page);
    const before = requests.length;
    await pickLlm(page, "qa-beta", "s2-menu.png");
    const writes = requests.slice(before).filter((r) => r.startsWith("POST"));
    await gotoHome(page);
    const afterReload = await pills(page);
    await page.screenshot({ path: `${OUT}/s2-after-reload.png` });
    record("s2 named profile on home", { shown, writes, afterReload, reviewerRef: (await agentProfile("qa-reviewer")).llm_profile_ref });
  }

  if (STEPS.includes("s3")) {
    // Edit `default` in Settings → Agents, pick qa-gamma, save.
    await reset("default");
    await page.goto(`${FRONT}/settings/agents`, { waitUntil: "domcontentloaded" });
    const row = page.getByTestId("agent-profile-row").filter({ hasText: /^default/ }).first();
    await row.waitFor({ timeout: 60_000 });
    await row.getByTestId("agent-profile-menu-trigger").click();
    await page.getByTestId("agent-profile-edit").click();
    const selector = page.getByTestId("agent-profile-llm-selector");
    await selector.waitFor({ timeout: 60_000 });
    await page.waitForTimeout(2000);
    const opened = {
      nameDisabled: await page.getByTestId("agent-profile-name-input").isDisabled(),
      llmShown: await selector.inputValue(),
      defaultNote: await page.getByTestId("agent-profile-llm-default-note").count(),
    };
    await page.screenshot({ path: `${OUT}/s3-editor.png`, fullPage: true });
    await selector.click();
    await selector.fill("qa-gamma");
    await page.getByRole("option", { name: /qa-gamma/ }).first().click();
    const before = requests.length;
    await page.getByTestId("save-agent-profile-btn").click();
    await page.waitForTimeout(5000);
    const writes = requests.slice(before).filter((r) => r.startsWith("POST"));
    const saved = await agentProfile("default");
    record("s3 edit default", {
      opened,
      writes,
      saved: { llm_profile_ref: saved.llm_profile_ref, mcp_server_refs: saved.mcp_server_refs, secret_refs: saved.secret_refs },
      orgActive: await orgActiveLlm(),
    });
  }
} catch (error) {
  record("error", { message: String(error).slice(0, 800) });
  await page.screenshot({ path: `${OUT}/error.png` }).catch(() => undefined);
} finally {
  writeFileSync(`${OUT}/results.json`, JSON.stringify({ mode: MODE, dry: DRY, results, starts, blocked, requests, consoleErrors }, null, 2));
  await browser.close();
}
console.log(`starts=${JSON.stringify(starts)} blocked=${blocked.length} consoleErrors=${consoleErrors.length}`);
