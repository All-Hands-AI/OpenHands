import React from "react";
import { createRoot } from "react-dom/client";
import { createInstance } from "i18next";
import {
  I18nextProvider,
  initReactI18next,
  useTranslation,
} from "react-i18next";
import {
  ArrowRight,
  Check,
  FlaskConical,
  Layers2,
  MessageSquare,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import type { ObservationEvent } from "#/types/agent-server/core";
import type { MCPToolObservation } from "#/types/agent-server/core/base/observation";
import type { MCPAppArtifacts, MCPAppHost, MCPAppScope } from "#/types/mcp-app";
import { GenericEventMessageWrapper } from "#/components/conversation-events/chat/event-message-components/generic-event-message-wrapper";
import { MCPAppHostProvider } from "#/components/features/mcp-apps/mcp-app-host-context";
import { AvailableLanguages, setI18n, translationResources } from "#/i18n";
import { I18nKey } from "#/i18n/declaration";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { cn } from "#/utils/utils";
import APP_HTML from "./market-app.html?raw";
import "#/tailwind.css";
import "#/index.css";
import "./demo.css";

const LANGUAGE_PARAMETER = "lang";
const requestedLanguage = new URL(window.location.href).searchParams.get(
  LANGUAGE_PARAMETER,
);
const initialLanguage =
  AvailableLanguages.find((language) => language.value === requestedLanguage)
    ?.value ?? "en";
const appTranslations = Object.fromEntries(
  Object.entries(translationResources).map(([locale, resources]) => [
    locale,
    Object.fromEntries(
      Object.entries(resources).filter(([key]) =>
        key.startsWith("MCP$DEMO_APP_"),
      ),
    ),
  ]),
);
// Escape '<' so translation text cannot terminate the inert JSON script element.
const localizedAppHTML = APP_HTML.replace("__MCP_DEMO_TRANSLATIONS__", () =>
  JSON.stringify(appTranslations).replaceAll("<", "\\u003c"),
);

const demoI18n = createInstance();
await demoI18n.use(initReactI18next).init({
  lng: initialLanguage,
  supportedLngs: AvailableLanguages.map((language) => language.value),
  fallbackLng: "en",
  ns: ["openhands"],
  defaultNS: "openhands",
  resources: Object.fromEntries(
    Object.entries(translationResources).map(([language, translations]) => [
      language,
      { openhands: translations },
    ]),
  ),
  interpolation: { escapeValue: false },
});
setI18n(demoI18n);

const event: ObservationEvent<MCPToolObservation> = {
  id: "mcp-result-demo",
  timestamp: "2026-10-13T12:00:00+08:00",
  source: "environment",
  tool_name: "show_market_summary",
  tool_call_id: "market-call-1",
  action_id: "market-action-1",
  observation: {
    kind: "MCPToolObservation",
    tool_name: "show_market_summary",
    content: [
      {
        type: "text",
        text: "The simulated chart is ready. The original text result is preserved.",
      },
    ],
    is_error: false,
  },
};

const artifacts: MCPAppArtifacts = new Map([
  [
    event.id,
    {
      tool: {
        name: "show_market_summary",
        _meta: { ui: { resourceUri: "ui://market/summary" } },
      },
      toolInput: { symbol: "OPEN" },
      toolResult: {
        content: [{ type: "text", text: "OPEN 128.40, up 3.18%" }],
        structuredContent: { symbol: "OPEN", price: "128.40" },
        _meta: { privateSelection: "local-only" },
      },
    },
  ],
]);

function Demo() {
  const { t, i18n } = useTranslation("openhands", { i18n: demoI18n });
  const locale = i18n.resolvedLanguage ?? "en";
  const demoCopy = {
    brand: "OpenHands",
    canvas: "Agent Canvas",
    local: t(I18nKey.MCP$DEMO_LOCAL),
    issue: "Issue #16620",
    eyebrow: "MCP Apps",
    title: t(I18nKey.MCP$DEMO_TITLE),
    description: t(I18nKey.MCP$DEMO_DESCRIPTION),
    conversation: t(I18nKey.MCP$DEMO_CONVERSATION),
    mainSession: t(I18nKey.MCP$DEMO_MAIN_SESSION),
    planningSession: t(I18nKey.MCP$DEMO_PLANNING_SESSION),
    you: t(I18nKey.MCP$DEMO_YOU),
    prompt: t(I18nKey.MCP$DEMO_PROMPT),
    controls: t(I18nKey.MCP$DEMO_CONTROLS),
    controlDescription: t(I18nKey.MCP$DEMO_CONTROL_DESCRIPTION),
    switchMode: t(I18nKey.MCP$DEMO_SWITCH_MODE),
    switchBack: t(I18nKey.MCP$DEMO_SWITCH_BACK),
    activeDescription: t(I18nKey.MCP$DEMO_ACTIVE_DESCRIPTION),
    readOnlyDescription: t(I18nKey.MCP$DEMO_READ_ONLY_DESCRIPTION),
    diagnostics: t(I18nKey.MCP$DEMO_DIAGNOSTICS),
    spoofMessage: t(I18nKey.MCP$DEMO_SPOOF_MESSAGE),
    spoofDescription: t(I18nKey.MCP$DEMO_SPOOF_DESCRIPTION),
    activity: t(I18nKey.MCP$DEMO_ACTIVITY),
    activityDescription: t(I18nKey.MCP$DEMO_ACTIVITY_DESCRIPTION),
    emptyLog: t(I18nKey.MCP$DEMO_EMPTY_LOG),
    isolation: t(I18nKey.MCP$DEMO_ISOLATION),
    binding: t(I18nKey.MCP$DEMO_BINDING),
    textResult: t(I18nKey.MCP$DEMO_TEXT_RESULT),
    footer: t(I18nKey.MCP$DEMO_FOOTER),
  };
  const localizedEvent = React.useMemo(
    () => ({
      ...event,
      observation: {
        ...event.observation,
        content: [
          {
            type: "text" as const,
            text: t(I18nKey.MCP$DEMO_ORIGINAL_TEXT_RESULT),
          },
        ],
      },
    }),
    [t],
  );
  React.useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = i18n.dir(locale);
    document.title = t(I18nKey.MCP$DEMO_TITLE);
  }, [i18n, locale, t]);
  const changeLanguage = (language: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set(LANGUAGE_PARAMETER, language);
    window.history.replaceState(null, "", url);
    void i18n.changeLanguage(language);
  };
  const [logs, setLogs] = React.useState<string[]>([]);
  const [writableConversationId, setWritableConversationId] = React.useState<
    string | null
  >("conversation-main");
  const sessionCount = React.useRef(0);
  const appendLog = React.useCallback((message: string) => {
    setLogs((current) => [...current, message]);
  }, []);

  const host = React.useMemo<MCPAppHost>(
    () => ({
      sandboxUrl: "http://127.0.0.1:3102/sandbox.html",
      async open(binding, { signal }) {
        signal.throwIfAborted();
        sessionCount.current += 1;
        appendLog(
          `Host session #${sessionCount.current}: ${binding.ownerConversationId} / ${binding.toolCallId}`,
        );
        return {
          async readResource(uri, options) {
            options.signal.throwIfAborted();
            appendLog(`resources/read ${uri}`);
            return {
              contents: [
                {
                  uri,
                  mimeType: "text/html;profile=mcp-app",
                  text: localizedAppHTML,
                },
              ],
            };
          },
          async callTool(params, options) {
            options.signal.throwIfAborted();
            appendLog(`tools/call ${params.name}`);
            return {
              content: [
                {
                  type: "text",
                  text: demoI18n.t(I18nKey.MCP$DEMO_REFRESHED_TEXT_RESULT),
                },
              ],
              structuredContent: { price: "129.05" },
            };
          },
          async updateModelContext(params, options) {
            options.signal.throwIfAborted();
            const text = params.content?.find((item) => item.type === "text");
            appendLog(`updateModelContext ${text?.text ?? ""}`);
            return {};
          },
          async sendMessage(params, options) {
            options.signal.throwIfAborted();
            const text = params.content.find((item) => item.type === "text");
            appendLog(`message ${text?.text ?? ""}`);
            return {};
          },
          dispose() {
            appendLog("session disposed");
          },
        };
      },
    }),
    [appendLog],
  );

  const scope = React.useMemo<MCPAppScope>(
    () => ({
      backendId: "demo-backend",
      orgId: null,
      connectionRevision: 1,
      conversationId: "conversation-main",
      planningConversationId: "conversation-plan",
      writableConversationId,
    }),
    [writableConversationId],
  );

  return (
    <I18nextProvider i18n={demoI18n}>
      <MCPAppHostProvider host={host} scope={scope} artifacts={artifacts}>
        <div data-testid="mcp-demo-shell" className="min-h-dvh text-foreground">
          <header className="border-b border-border-subtle">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-8">
              <div className="flex items-center gap-3">
                <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-on-primary">
                  <Layers2 className="size-5" aria-hidden="true" />
                </span>
                <span className="text-base font-semibold">
                  {demoCopy.brand}
                </span>
                <span className="ms-3 hidden border-s border-border ps-4 text-sm text-muted sm:block">
                  {demoCopy.canvas}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-xs text-muted">
                  <span>{t(I18nKey.MCP$DEMO_LANGUAGE_LABEL)}</span>
                  <select
                    data-testid="language-select"
                    value={locale}
                    onChange={(event) => changeLanguage(event.target.value)}
                    className="max-w-40 rounded-md border border-border-subtle bg-surface px-2 py-1.5 text-text-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                  >
                    {AvailableLanguages.map((language) => (
                      <option key={language.value} value={language.value}>
                        {language.label}
                      </option>
                    ))}
                  </select>
                </label>
                <span className="flex items-center gap-2 rounded-full border border-border-subtle px-3 py-1 text-xs text-text-secondary">
                  <FlaskConical
                    className="size-3.5 text-primary"
                    aria-hidden="true"
                  />
                  {demoCopy.local}
                </span>
              </div>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-5 pb-10 pt-10 sm:px-8 sm:pt-12">
            <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
              <div>
                <p className="mb-3 flex items-center gap-3 text-sm text-primary">
                  {demoCopy.eyebrow}
                  <span className="rounded-md border border-border-subtle px-2 py-0.5 font-mono text-xs text-muted">
                    {demoCopy.issue}
                  </span>
                </p>
                <h1 className="text-balance text-3xl font-semibold leading-tight sm:text-4xl">
                  {demoCopy.title}
                </h1>
                <p className="mt-3 max-w-2xl text-pretty text-sm leading-6 text-text-secondary sm:text-base">
                  {demoCopy.description}
                </p>
              </div>
              <ul className="flex flex-wrap gap-4 text-xs text-muted">
                {[
                  demoCopy.isolation,
                  demoCopy.binding,
                  demoCopy.textResult,
                ].map((label) => (
                  <li key={label} className="flex items-center gap-1.5">
                    <Check
                      className="size-3.5 text-primary"
                      aria-hidden="true"
                    />
                    {label}
                  </li>
                ))}
              </ul>
            </div>
            <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
              <section
                data-mcp-demo-card
                className="min-w-0 overflow-hidden rounded-xl border border-border-subtle bg-surface"
              >
                <div className="flex items-center justify-between gap-4 border-b border-border-subtle px-5 py-4 sm:px-6">
                  <h2 className="flex items-center gap-2 text-balance text-sm font-medium">
                    <MessageSquare
                      className="size-4 text-muted"
                      aria-hidden="true"
                    />
                    {demoCopy.conversation}
                  </h2>
                  <span className="rounded-full bg-surface-raised px-2.5 py-1 text-xs text-text-secondary">
                    {writableConversationId === "conversation-main"
                      ? demoCopy.mainSession
                      : demoCopy.planningSession}
                  </span>
                </div>
                <div className="p-5 sm:p-6">
                  <div className="mb-6 flex items-start gap-3 border-b border-border-subtle pb-6">
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface-raised text-xs text-text-secondary">
                      {demoCopy.you}
                    </span>
                    <p className="pt-1 text-pretty text-sm leading-6">
                      {demoCopy.prompt}
                    </p>
                  </div>
                  <GenericEventMessageWrapper
                    event={localizedEvent}
                    isLastMessage
                  />
                </div>
              </section>
              <aside className="flex min-w-0 flex-col gap-4">
                <section
                  className="rounded-xl border border-border-subtle bg-surface p-5"
                  data-mcp-demo-controls
                >
                  <h2 className="mb-2 text-balance text-sm font-medium">
                    {demoCopy.controls}
                  </h2>
                  <p className="mb-5 text-pretty text-xs leading-5 text-muted">
                    {demoCopy.controlDescription}
                  </p>
                  <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-border-subtle bg-canvas-base p-3">
                    <ShieldCheck
                      className="mt-0.5 size-4 shrink-0 text-primary"
                      aria-hidden="true"
                    />
                    <p
                      className="text-pretty text-xs leading-5 text-text-secondary"
                      role="status"
                    >
                      {writableConversationId === "conversation-main"
                        ? demoCopy.activeDescription
                        : demoCopy.readOnlyDescription}
                    </p>
                  </div>
                  <ModalButton
                    testId="mode-switch"
                    text={
                      writableConversationId === "conversation-main"
                        ? demoCopy.switchMode
                        : demoCopy.switchBack
                    }
                    icon={<ArrowRight className="size-4" aria-hidden="true" />}
                    className="w-full rounded-lg border border-border bg-surface-raised px-3 text-foreground hover:bg-interactive-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                    onClick={() =>
                      setWritableConversationId((current) =>
                        current === "conversation-main"
                          ? "conversation-plan"
                          : "conversation-main",
                      )
                    }
                  />
                </section>
                <section className="overflow-hidden rounded-xl border border-border-subtle bg-surface">
                  <div className="border-b border-border-subtle px-5 py-4">
                    <h2 className="flex items-center gap-2 text-balance text-sm font-medium">
                      <Terminal
                        className="size-4 text-muted"
                        aria-hidden="true"
                      />
                      {demoCopy.activity}
                      <span className="ms-auto rounded-md bg-surface-raised px-1.5 font-mono text-xs tabular-nums text-muted">
                        {logs.length}
                      </span>
                    </h2>
                    <p className="mt-1.5 text-pretty text-xs text-muted">
                      {demoCopy.activityDescription}
                    </p>
                  </div>
                  <pre
                    data-testid="host-log"
                    className={cn(
                      "max-h-64 min-h-36 overflow-auto whitespace-pre-wrap break-words bg-surface-deep p-5 font-mono text-xs leading-6 text-text-secondary",
                      !logs.length && "text-muted",
                    )}
                  >
                    {logs.map((entry, index) => (
                      <span
                        key={`${index}-${entry}`}
                        className="mb-2 flex gap-3 last:mb-0"
                      >
                        <span
                          className="shrink-0 text-text-dim"
                          aria-hidden="true"
                        >
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <span>
                          {entry}
                          {"\n"}
                        </span>
                      </span>
                    ))}
                    {!logs.length && demoCopy.emptyLog}
                  </pre>
                </section>
                <details className="rounded-xl border border-border-subtle px-5 py-4">
                  <summary className="cursor-pointer text-sm text-text-secondary focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-focus">
                    {demoCopy.diagnostics}
                  </summary>
                  <p className="mb-3 mt-3 text-pretty text-xs leading-5 text-muted">
                    {demoCopy.spoofDescription}
                  </p>
                  <ModalButton
                    testId="spoof-message"
                    text={demoCopy.spoofMessage}
                    className="w-full rounded-lg border border-border px-3 text-text-secondary hover:bg-surface-raised focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                    onClick={() =>
                      window.postMessage(
                        {
                          jsonrpc: "2.0",
                          id: "spoof",
                          method: "tools/call",
                          params: { name: "refresh_market" },
                        },
                        window.location.origin,
                      )
                    }
                  />
                </details>
              </aside>
            </div>
            <p className="mt-6 text-pretty text-xs text-muted">
              {demoCopy.footer}
            </p>
          </main>
        </div>
      </MCPAppHostProvider>
    </I18nextProvider>
  );
}

createRoot(document.getElementById("root")!).render(<Demo />);
