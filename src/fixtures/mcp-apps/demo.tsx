import React from "react";
import { createRoot } from "react-dom/client";
import { createInstance } from "i18next";
import { I18nextProvider, initReactI18next } from "react-i18next";
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
import { setI18n, translationResources } from "#/i18n";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { cn } from "#/utils/utils";
import APP_HTML from "./market-app.html?raw";
import "#/tailwind.css";
import "#/index.css";
import "./demo.css";

const DEMO_COPY = {
  brand: "OpenHands",
  canvas: "Agent Canvas",
  local: "本地演示",
  issue: "Issue #16620",
  eyebrow: "MCP Apps",
  title: "让工具结果，成为交互界面。",
  description: "在对话中查看图表、刷新数据，或把你的选择带回模型。",
  conversation: "会话预览",
  mainSession: "主会话",
  planningSession: "规划会话",
  you: "你",
  prompt: "查看 OPEN 的行情，并生成交互图表。",
  controls: "会话控制",
  controlDescription: "切换会话，检查界面的写入权限。",
  switchMode: "切换到规划会话",
  switchBack: "回到主会话",
  activeDescription: "主会话可接收工具调用与后续消息。",
  readOnlyDescription: "图表仍可查看，原会话的写入权限已收回。",
  diagnostics: "边界检查",
  spoofMessage: "测试窗口来源校验",
  spoofDescription: "发送来自其他窗口的消息，Host 应忽略它。",
  activity: "Host activity",
  activityDescription: "查看界面与 Host 的调用记录。",
  emptyLog: "等待界面连接…",
  isolation: "沙箱隔离",
  binding: "会话绑定",
  textResult: "保留文本结果",
  footer: "本地原型 · 使用模拟数据，尚未连接 Agent Server",
};

const demoI18n = createInstance();
await demoI18n.use(initReactI18next).init({
  lng: "zh-CN",
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
      { type: "text", text: "模拟图表已准备好，原始文本结果仍然保留。" },
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
                  text: APP_HTML,
                },
              ],
            };
          },
          async callTool(params, options) {
            options.signal.throwIfAborted();
            appendLog(`tools/call ${params.name}`);
            return {
              content: [{ type: "text", text: "Refreshed locally" }],
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
                  {DEMO_COPY.brand}
                </span>
                <span className="ml-3 hidden border-l border-border pl-4 text-sm text-muted sm:block">
                  {DEMO_COPY.canvas}
                </span>
              </div>
              <span className="flex items-center gap-2 rounded-full border border-border-subtle px-3 py-1 text-xs text-text-secondary">
                <FlaskConical
                  className="size-3.5 text-primary"
                  aria-hidden="true"
                />
                {DEMO_COPY.local}
              </span>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-5 pb-10 pt-10 sm:px-8 sm:pt-12">
            <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
              <div>
                <p className="mb-3 flex items-center gap-3 text-sm text-primary">
                  {DEMO_COPY.eyebrow}
                  <span className="rounded-md border border-border-subtle px-2 py-0.5 font-mono text-xs text-muted">
                    {DEMO_COPY.issue}
                  </span>
                </p>
                <h1 className="text-balance text-3xl font-semibold leading-tight sm:text-4xl">
                  {DEMO_COPY.title}
                </h1>
                <p className="mt-3 max-w-2xl text-pretty text-sm leading-6 text-text-secondary sm:text-base">
                  {DEMO_COPY.description}
                </p>
              </div>
              <ul className="flex flex-wrap gap-4 text-xs text-muted">
                {[
                  DEMO_COPY.isolation,
                  DEMO_COPY.binding,
                  DEMO_COPY.textResult,
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
                    {DEMO_COPY.conversation}
                  </h2>
                  <span className="rounded-full bg-surface-raised px-2.5 py-1 text-xs text-text-secondary">
                    {writableConversationId === "conversation-main"
                      ? DEMO_COPY.mainSession
                      : DEMO_COPY.planningSession}
                  </span>
                </div>
                <div className="p-5 sm:p-6">
                  <div className="mb-6 flex items-start gap-3 border-b border-border-subtle pb-6">
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface-raised text-xs text-text-secondary">
                      {DEMO_COPY.you}
                    </span>
                    <p className="pt-1 text-pretty text-sm leading-6">
                      {DEMO_COPY.prompt}
                    </p>
                  </div>
                  <GenericEventMessageWrapper event={event} isLastMessage />
                </div>
              </section>
              <aside className="flex min-w-0 flex-col gap-4">
                <section
                  className="rounded-xl border border-border-subtle bg-surface p-5"
                  data-mcp-demo-controls
                >
                  <h2 className="mb-2 text-balance text-sm font-medium">
                    {DEMO_COPY.controls}
                  </h2>
                  <p className="mb-5 text-pretty text-xs leading-5 text-muted">
                    {DEMO_COPY.controlDescription}
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
                        ? DEMO_COPY.activeDescription
                        : DEMO_COPY.readOnlyDescription}
                    </p>
                  </div>
                  <ModalButton
                    testId="mode-switch"
                    text={
                      writableConversationId === "conversation-main"
                        ? DEMO_COPY.switchMode
                        : DEMO_COPY.switchBack
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
                      {DEMO_COPY.activity}
                      <span className="ml-auto rounded-md bg-surface-raised px-1.5 font-mono text-xs tabular-nums text-muted">
                        {logs.length}
                      </span>
                    </h2>
                    <p className="mt-1.5 text-pretty text-xs text-muted">
                      {DEMO_COPY.activityDescription}
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
                    {!logs.length && DEMO_COPY.emptyLog}
                  </pre>
                </section>
                <details className="rounded-xl border border-border-subtle px-5 py-4">
                  <summary className="cursor-pointer text-sm text-text-secondary focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-focus">
                    {DEMO_COPY.diagnostics}
                  </summary>
                  <p className="mb-3 mt-3 text-pretty text-xs leading-5 text-muted">
                    {DEMO_COPY.spoofDescription}
                  </p>
                  <ModalButton
                    testId="spoof-message"
                    text={DEMO_COPY.spoofMessage}
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
              {DEMO_COPY.footer}
            </p>
          </main>
        </div>
      </MCPAppHostProvider>
    </I18nextProvider>
  );
}

createRoot(document.getElementById("root")!).render(<Demo />);
