import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ErrorCode,
  type CallToolResult,
  type JSONRPCMessage,
} from "@modelcontextprotocol/sdk/types.js";
import { LATEST_PROTOCOL_VERSION } from "@modelcontextprotocol/ext-apps/app-bridge";
import type { MCPAppDescriptor, MCPAppSession } from "#/types/mcp-app";
import { mountMCPAppBridge } from "#/components/features/mcp-apps/mcp-app-bridge";

const HOST_ORIGIN = "https://canvas.example.com";
const SANDBOX_ORIGIN = "https://sandbox.example.com";
const descriptor: MCPAppDescriptor = {
  resourceUri: "ui://chart",
  tool: { name: "chart", _meta: { ui: { resourceUri: "ui://chart" } } },
  toolInput: { symbol: "OPEN" },
  toolResult: {
    content: [{ type: "text", text: "Chart ready" }],
    structuredContent: { points: [1, 2] },
    _meta: { privateSelection: "OPEN" },
  },
};

function createHarness(sessionOverrides: Partial<MCPAppSession> = {}) {
  const hostWindow = Object.assign(new EventTarget(), {
    location: new URL(HOST_ORIGIN),
  });
  vi.stubGlobal("window", hostWindow);
  const messages: JSONRPCMessage[] = [];
  const childWindow = {
    postMessage: vi.fn((message: JSONRPCMessage, _targetOrigin: string) => {
      messages.push(message);
      if (
        "method" in message &&
        "id" in message &&
        message.method === "ui/resource-teardown"
      ) {
        queueMicrotask(() =>
          receive({ jsonrpc: "2.0", id: message.id, result: {} }),
        );
      }
    }),
  };
  const iframe = {
    contentWindow: childWindow,
    src: "",
    setAttribute: vi.fn(),
  } as unknown as HTMLIFrameElement;
  const controller = new AbortController();
  let writable = true;
  const session: MCPAppSession = {
    readResource: vi.fn(async () => ({ contents: [] })),
    ...sessionOverrides,
  };
  const options = {
    iframe,
    sandboxUrl: `${SANDBOX_ORIGIN}/sandbox.html`,
    resource: {
      contents: [
        {
          uri: descriptor.resourceUri,
          mimeType: "text/html;profile=mcp-app",
          text: "<!doctype html><html><body>Chart</body></html>",
        },
      ],
    },
    descriptor,
    session,
    signal: controller.signal,
    isWritable: () => writable,
    onReady: vi.fn(),
    onError: vi.fn(),
    onSizeChange: vi.fn(),
  };
  function receive(
    data: unknown,
    origin = SANDBOX_ORIGIN,
    source: unknown = childWindow,
  ) {
    hostWindow.dispatchEvent(
      Object.assign(new Event("message"), { data, origin, source }),
    );
  }
  async function initialize() {
    receive({
      jsonrpc: "2.0",
      method: "ui/notifications/sandbox-proxy-ready",
      params: {},
    });
    await vi.waitFor(() =>
      expect(
        messages.some(
          (m) =>
            "method" in m &&
            m.method === "ui/notifications/sandbox-resource-ready",
        ),
      ).toBe(true),
    );
    receive({
      jsonrpc: "2.0",
      id: "init",
      method: "ui/initialize",
      params: {
        protocolVersion: LATEST_PROTOCOL_VERSION,
        appInfo: { name: "chart-app", version: "1" },
        appCapabilities: {},
      },
    });
    await vi.waitFor(() =>
      expect(
        messages.some((m) => "id" in m && m.id === "init" && "result" in m),
      ).toBe(true),
    );
    receive({
      jsonrpc: "2.0",
      method: "ui/notifications/initialized",
      params: {},
    });
    await vi.waitFor(() => expect(options.onReady).toHaveBeenCalledOnce());
  }
  return {
    childWindow,
    controller,
    hostWindow,
    iframe,
    initialize,
    messages,
    options,
    receive,
    session,
    revokeWrites: () => {
      writable = false;
    },
  };
}

beforeEach(() => vi.restoreAllMocks());
afterEach(() => vi.unstubAllGlobals());

// @spec MCA-003 — MCP apps initialize through an isolated, validated bridge
describe("mountMCPAppBridge", () => {
  it("initializes the real protocol and sends input before the complete result", async () => {
    const harness = createHarness();
    const mounted = await mountMCPAppBridge(harness.options);
    await harness.initialize();

    const notifications = harness.messages.filter(
      (m) => "method" in m && m.method.startsWith("ui/notifications/tool-"),
    );
    expect(notifications).toEqual([
      {
        jsonrpc: "2.0",
        method: "ui/notifications/tool-input",
        params: { arguments: descriptor.toolInput },
      },
      {
        jsonrpc: "2.0",
        method: "ui/notifications/tool-result",
        params: descriptor.toolResult,
      },
    ]);
    expect(new URL(harness.iframe.src).searchParams.get("parentOrigin")).toBe(
      HOST_ORIGIN,
    );
    expect(
      harness.childWindow.postMessage.mock.calls.every(
        (call) => call[1] === SANDBOX_ORIGIN,
      ),
    ).toBe(true);
    await mounted.dispose();
  });

  it("ignores spoofed origins and windows, and rejects malformed protocol messages", async () => {
    const harness = createHarness();
    const mounted = await mountMCPAppBridge(harness.options);
    const ready = {
      jsonrpc: "2.0",
      method: "ui/notifications/sandbox-proxy-ready",
      params: {},
    };
    harness.receive(ready, HOST_ORIGIN);
    harness.receive(ready, SANDBOX_ORIGIN, {});
    await new Promise((resolve) => setImmediate(resolve));
    expect(harness.messages).toEqual([]);

    harness.receive({ jsonrpc: "2.0", id: [], method: "tools/call" });
    expect(harness.options.onError).toHaveBeenCalledOnce();
    await mounted.dispose();
  });

  // @spec MCA-004 — Each UI call stays bound to its current session and write scope
  it("rechecks write permission and only advertises implemented capabilities", async () => {
    const callTool = vi.fn<NonNullable<MCPAppSession["callTool"]>>(
      async () => ({ content: [] }),
    );
    const harness = createHarness({ callTool });
    const mounted = await mountMCPAppBridge(harness.options);
    await harness.initialize();
    const initialization = harness.messages.find(
      (m) => "id" in m && m.id === "init",
    );
    expect(initialization).toMatchObject({
      result: { hostCapabilities: { serverTools: {}, serverResources: {} } },
    });
    expect(initialization).not.toMatchObject({
      result: { hostCapabilities: { message: {} } },
    });

    harness.receive({
      jsonrpc: "2.0",
      id: "allowed",
      method: "tools/call",
      params: { name: "refresh", arguments: {} },
    });
    await vi.waitFor(() => expect(callTool).toHaveBeenCalledOnce());
    expect(callTool.mock.calls[0][1].signal).toBeInstanceOf(AbortSignal);
    harness.revokeWrites();
    harness.receive({
      jsonrpc: "2.0",
      id: "denied",
      method: "tools/call",
      params: { name: "refresh" },
    });
    harness.receive({
      jsonrpc: "2.0",
      id: "unsupported",
      method: "ui/message",
      params: { role: "user", content: [{ type: "text", text: "Follow up" }] },
    });
    await vi.waitFor(() =>
      expect(harness.messages).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            id: "denied",
            error: expect.objectContaining({ code: ErrorCode.InvalidRequest }),
          }),
          expect.objectContaining({
            id: "unsupported",
            error: expect.objectContaining({ code: ErrorCode.MethodNotFound }),
          }),
        ]),
      ),
    );
    expect(callTool).toHaveBeenCalledOnce();
    await mounted.dispose();
  });

  it("rejects non-text context and messages instead of claiming to support them", async () => {
    const sendMessage = vi.fn(async () => ({}));
    const updateModelContext = vi.fn(async () => ({}));
    const harness = createHarness({ sendMessage, updateModelContext });
    const mounted = await mountMCPAppBridge(harness.options);
    await harness.initialize();

    harness.receive({
      jsonrpc: "2.0",
      id: "image",
      method: "ui/message",
      params: {
        role: "user",
        content: [{ type: "image", data: "aGVsbG8=", mimeType: "image/png" }],
      },
    });
    harness.receive({
      jsonrpc: "2.0",
      id: "structured",
      method: "ui/update-model-context",
      params: { structuredContent: { selection: 1 } },
    });
    await vi.waitFor(() =>
      expect(harness.messages).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            id: "image",
            error: expect.objectContaining({ code: ErrorCode.InvalidParams }),
          }),
          expect.objectContaining({
            id: "structured",
            error: expect.objectContaining({ code: ErrorCode.InvalidParams }),
          }),
        ]),
      ),
    );
    expect(sendMessage).not.toHaveBeenCalled();
    expect(updateModelContext).not.toHaveBeenCalled();
    await mounted.dispose();
  });

  it("aborts pending UI work, tears down once, and removes its message listener", async () => {
    let requestSignal: AbortSignal | undefined;
    let resolveCall: ((result: CallToolResult) => void) | undefined;
    const callTool = vi.fn<NonNullable<MCPAppSession["callTool"]>>(
      (_params, { signal }) => {
        requestSignal = signal;
        return new Promise<CallToolResult>((resolve) => {
          resolveCall = resolve;
        });
      },
    );
    const harness = createHarness({ callTool });
    const removeListener = vi.spyOn(harness.hostWindow, "removeEventListener");
    const mounted = await mountMCPAppBridge(harness.options);
    await harness.initialize();
    harness.receive({
      jsonrpc: "2.0",
      id: "pending",
      method: "tools/call",
      params: { name: "refresh" },
    });
    await vi.waitFor(() => expect(requestSignal).toBeDefined());
    harness.controller.abort();
    await mounted.dispose();
    await mounted.dispose();
    resolveCall?.({ content: [] });
    await new Promise((resolve) => setImmediate(resolve));

    expect(requestSignal?.aborted).toBe(true);
    expect(
      harness.messages.filter(
        (m) => "method" in m && m.method === "ui/resource-teardown",
      ),
    ).toHaveLength(1);
    expect(removeListener).toHaveBeenCalledWith(
      "message",
      expect.any(Function),
    );
    expect(
      harness.messages.some(
        (m) => "id" in m && m.id === "pending" && "result" in m,
      ),
    ).toBe(false);
    const count = harness.messages.length;
    harness.receive({
      jsonrpc: "2.0",
      method: "ui/notifications/size-changed",
      params: { height: 400 },
    });
    expect(harness.messages).toHaveLength(count);
    expect(harness.options.onSizeChange).not.toHaveBeenCalled();
  });

  it.each([
    HOST_ORIGIN,
    "javascript:alert(1)",
    "https://user:pass@sandbox.example.com/sandbox.html",
  ])(
    "rejects an unsafe sandbox URL before loading HTML: %s",
    async (sandboxUrl) => {
      const harness = createHarness();
      await expect(
        mountMCPAppBridge({ ...harness.options, sandboxUrl }),
      ).rejects.toThrow();
      expect(harness.iframe.src).toBe("");
      expect(harness.messages).toEqual([]);
    },
  );

  it("rejects an invalid tool result before loading the sandbox", async () => {
    const harness = createHarness();
    const invalidDescriptor = {
      ...descriptor,
      toolResult: { content: [{ type: "text" }] },
    } as unknown as MCPAppDescriptor;

    await expect(
      mountMCPAppBridge({
        ...harness.options,
        descriptor: invalidDescriptor,
      }),
    ).rejects.toThrow("Invalid MCP tool result");
    expect(harness.iframe.src).toBe("");
    expect(harness.messages).toEqual([]);
  });

  it.each([
    { ui: { csp: { connectDomains: ["https://api.example.com"] } } },
    { ui: { permissions: { camera: {} } } },
  ])(
    "keeps unsupported resource permissions out of the sandbox: %j",
    async (_meta) => {
      const harness = createHarness();
      const resource = {
        contents: [{ ...harness.options.resource.contents[0], _meta }],
      };
      await expect(
        mountMCPAppBridge({ ...harness.options, resource }),
      ).rejects.toThrow();
      expect(harness.iframe.src).toBe("");
    },
  );
});
