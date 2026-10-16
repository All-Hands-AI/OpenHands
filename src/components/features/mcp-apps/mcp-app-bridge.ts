import {
  AppBridge,
  RESOURCE_MIME_TYPE,
  type McpUiHostCapabilities,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps/app-bridge";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import {
  ErrorCode,
  CallToolResultSchema,
  JSONRPCMessageSchema,
  McpError,
  ReadResourceResultSchema,
  type JSONRPCMessage,
  type ReadResourceResult,
} from "@modelcontextprotocol/sdk/types.js";
import type { MCPAppDescriptor, MCPAppSession } from "#/types/mcp-app";

const MESSAGE_EVENT = "message";
const ABORT_EVENT = "abort";
const PARENT_ORIGIN_PARAMETER = "parentOrigin";
const OUTER_SANDBOX_PERMISSIONS = "allow-scripts allow-same-origin";
const INNER_SANDBOX_PERMISSIONS = "allow-scripts";
const TEARDOWN_TIMEOUT_MS = 1000;
const MAX_APP_HEIGHT = 4096;
const DEFAULT_APP_LOCALE = "en";
const HOST_INFO = { name: "OpenHands Agent Canvas", version: "1" };

interface MountMCPAppBridgeOptions {
  iframe: HTMLIFrameElement;
  locale: string;
  sandboxUrl: string;
  resource: ReadResourceResult;
  descriptor: MCPAppDescriptor;
  session: MCPAppSession;
  signal: AbortSignal;
  isWritable: () => boolean;
  onReady: () => void;
  onError: (error: unknown) => void;
  onSizeChange: (height: number) => void;
}

export interface MountedMCPAppBridge {
  dispose: () => Promise<void>;
  updateLocale: (locale: string) => void;
}

// @spec MCA-003 — The proxy transport authenticates both its window and origin
class SandboxTransport implements Transport {
  onmessage?: Transport["onmessage"];

  onerror?: Transport["onerror"];

  onclose?: Transport["onclose"];

  private closed = true;

  constructor(
    private readonly target: Window,
    private readonly origin: string,
    private readonly acceptsMessage: (message: JSONRPCMessage) => boolean,
  ) {}

  private readonly receive = (event: MessageEvent) => {
    if (
      this.closed ||
      event.source !== this.target ||
      event.origin !== this.origin
    ) {
      return;
    }
    const parsed = JSONRPCMessageSchema.safeParse(event.data);
    if (!parsed.success) {
      this.onerror?.(
        new McpError(ErrorCode.ParseError, "Invalid MCP app message"),
      );
      return;
    }
    if (this.acceptsMessage(parsed.data)) this.onmessage?.(parsed.data);
  };

  async start() {
    this.closed = false;
    window.addEventListener(MESSAGE_EVENT, this.receive);
  }

  async send(message: JSONRPCMessage) {
    if (this.closed) {
      throw new McpError(ErrorCode.InvalidRequest, "MCP app bridge is closed");
    }
    this.target.postMessage(message, this.origin);
  }

  async close() {
    if (this.closed) return;
    this.closed = true;
    window.removeEventListener(MESSAGE_EVENT, this.receive);
    this.onclose?.();
  }
}

function resourceHTML(resource: ReadResourceResult, uri: string): string {
  const content = resource.contents.find((item) => item.uri === uri);
  if (content?.mimeType !== RESOURCE_MIME_TYPE) {
    throw new McpError(ErrorCode.InvalidParams, "Unsupported MCP app resource");
  }
  const metadata = content._meta?.ui;
  if (metadata !== undefined) {
    if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) {
      throw new McpError(ErrorCode.InvalidParams, "Invalid MCP app metadata");
    }
    const { csp, permissions } = metadata as Record<string, unknown>;
    const isEmptyObject = (value: unknown): value is Record<string, unknown> =>
      !!value && typeof value === "object" && !Array.isArray(value);
    if (
      (csp !== undefined &&
        (!isEmptyObject(csp) ||
          Object.values(csp).some(
            (domains) => !Array.isArray(domains) || domains.length > 0,
          ))) ||
      (permissions !== undefined &&
        (!isEmptyObject(permissions) || Object.keys(permissions).length > 0))
    ) {
      throw new McpError(
        ErrorCode.InvalidParams,
        "MCP apps requiring external resources or permissions are unsupported",
      );
    }
  }
  if ("text" in content && typeof content.text === "string") {
    return content.text;
  }
  if ("blob" in content && typeof content.blob === "string") {
    try {
      const bytes = Uint8Array.from(atob(content.blob), (byte) =>
        byte.charCodeAt(0),
      );
      return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    } catch {
      throw new McpError(ErrorCode.InvalidParams, "Invalid MCP app HTML");
    }
  }
  throw new McpError(ErrorCode.InvalidParams, "Missing MCP app HTML");
}

// @spec MCA-003 — App lifecycle starts only inside a distinct HTTP(S) sandbox
export async function mountMCPAppBridge(
  options: MountMCPAppBridgeOptions,
): Promise<MountedMCPAppBridge> {
  const { iframe, descriptor, session, signal } = options;
  signal.throwIfAborted();
  const sandbox = new URL(options.sandboxUrl);
  if (
    !["https:", "http:"].includes(sandbox.protocol) ||
    sandbox.origin === window.location.origin ||
    sandbox.username ||
    sandbox.password
  ) {
    throw new McpError(
      ErrorCode.InvalidParams,
      "Invalid MCP app sandbox origin",
    );
  }
  const parsedResource = ReadResourceResultSchema.safeParse(options.resource);
  if (!parsedResource.success) {
    throw new McpError(
      ErrorCode.InvalidParams,
      "Invalid MCP app resource result",
    );
  }
  const parsedToolResult = CallToolResultSchema.safeParse(
    descriptor.toolResult,
  );
  if (!parsedToolResult.success) {
    throw new McpError(ErrorCode.InvalidParams, "Invalid MCP tool result");
  }
  const html = resourceHTML(parsedResource.data, descriptor.resourceUri);
  const target = iframe.contentWindow;
  if (!target) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      "MCP app iframe is unavailable",
    );
  }
  sandbox.searchParams.set(PARENT_ORIGIN_PARAMETER, window.location.origin);

  const capabilities: McpUiHostCapabilities = { serverResources: {} };
  if (session.callTool) capabilities.serverTools = {};
  if (session.sendMessage) capabilities.message = { text: {} };
  if (session.updateModelContext) {
    capabilities.updateModelContext = { text: {} };
  }
  const hostContext: McpUiHostContext = {
    platform: "web",
    displayMode: "inline",
    availableDisplayModes: ["inline"],
    locale: options.locale || DEFAULT_APP_LOCALE,
  };
  const bridge = new AppBridge(null, HOST_INFO, capabilities, { hostContext });
  const lifetime = new AbortController();
  let disposed = false;
  let initialized = false;
  let htmlSent = false;
  let disposal: Promise<void> | undefined;
  const reportError = (error: unknown) => {
    if (!disposed && !signal.aborted) options.onError(error);
  };
  const transport = new SandboxTransport(
    target,
    sandbox.origin,
    (message) => !disposed || !("method" in message),
  );
  bridge.onerror = reportError;

  // @spec MCA-004 — Pending callbacks cannot outlive their session or write scope
  const assertActive = (requestSignal: AbortSignal, writable: boolean) => {
    if (disposed || requestSignal.aborted || !initialized) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        "MCP app session is inactive",
      );
    }
    if (writable && !options.isWritable()) {
      throw new McpError(ErrorCode.InvalidRequest, "MCP app is read-only");
    }
  };
  const invoke = async <T>(
    callback: (requestSignal: AbortSignal) => Promise<T>,
    requestSignal: AbortSignal,
    writable: boolean,
  ): Promise<T> => {
    const combinedSignal = AbortSignal.any([
      signal,
      lifetime.signal,
      requestSignal,
    ]);
    assertActive(combinedSignal, writable);
    try {
      const result = await callback(combinedSignal);
      assertActive(combinedSignal, writable);
      return result;
    } catch (error) {
      if (error instanceof McpError) throw error;
      assertActive(combinedSignal, writable);
      throw new McpError(ErrorCode.InternalError, "MCP app request failed");
    }
  };
  const unsupported = () => {
    throw new McpError(
      ErrorCode.MethodNotFound,
      "MCP app capability unavailable",
    );
  };

  bridge.oncalltool = (params, extra) => {
    if (!session.callTool) return unsupported();
    const callTool = session.callTool.bind(session);
    return invoke(
      (requestSignal) => callTool(params, { signal: requestSignal }),
      extra.signal,
      true,
    );
  };
  bridge.onreadresource = (params, extra) =>
    invoke(
      (requestSignal) =>
        session.readResource(params.uri, { signal: requestSignal }),
      extra.signal,
      false,
    );
  bridge.onmessage = (params, extra) => {
    if (!session.sendMessage) return unsupported();
    if (params.content.some((content) => content.type !== "text")) {
      throw new McpError(
        ErrorCode.InvalidParams,
        "Unsupported MCP app content",
      );
    }
    const sendMessage = session.sendMessage.bind(session);
    return invoke(
      (requestSignal) => sendMessage(params, { signal: requestSignal }),
      extra.signal,
      true,
    );
  };
  bridge.onupdatemodelcontext = (params, extra) => {
    if (!session.updateModelContext) return unsupported();
    if (
      params.structuredContent !== undefined ||
      params.content?.some((content) => content.type !== "text")
    ) {
      throw new McpError(
        ErrorCode.InvalidParams,
        "Unsupported MCP app content",
      );
    }
    const updateContext = session.updateModelContext.bind(session);
    return invoke(
      (requestSignal) => updateContext(params, { signal: requestSignal }),
      extra.signal,
      true,
    );
  };

  const onSandboxReady = () => {
    if (disposed || signal.aborted || htmlSent) return;
    htmlSent = true;
    bridge
      .sendSandboxResourceReady({ html, sandbox: INNER_SANDBOX_PERMISSIONS })
      .catch(reportError);
  };
  const onInitialized = () => {
    if (disposed || signal.aborted || initialized) return;
    if (!htmlSent || !bridge.getAppVersion()) {
      reportError(
        new McpError(
          ErrorCode.InvalidRequest,
          "Invalid MCP app initialization",
        ),
      );
      return;
    }
    initialized = true;
    const sendData = async () => {
      await bridge.sendToolInput({ arguments: descriptor.toolInput });
      if (disposed || signal.aborted) return;
      await bridge.sendToolResult(parsedToolResult.data);
      if (!disposed && !signal.aborted) options.onReady();
    };
    sendData().catch(reportError);
  };
  const onSizeChange = ({ height }: { height?: number }) => {
    if (
      !disposed &&
      !signal.aborted &&
      initialized &&
      height !== undefined &&
      Number.isFinite(height) &&
      height > 0
    ) {
      options.onSizeChange(Math.min(MAX_APP_HEIGHT, Math.ceil(height)));
    }
  };
  bridge.addEventListener("sandboxready", onSandboxReady);
  bridge.addEventListener("initialized", onInitialized);
  bridge.addEventListener("sizechange", onSizeChange);

  const dispose = () => {
    if (disposal) return disposal;
    disposed = true;
    lifetime.abort();
    signal.removeEventListener(ABORT_EVENT, onAbort);
    disposal = (async () => {
      try {
        if (initialized) {
          await bridge.teardownResource({}, { timeout: TEARDOWN_TIMEOUT_MS });
        }
      } catch {
        // A crashed or unresponsive view must still release its transport.
      } finally {
        bridge.removeEventListener("sandboxready", onSandboxReady);
        bridge.removeEventListener("initialized", onInitialized);
        bridge.removeEventListener("sizechange", onSizeChange);
        try {
          await bridge.close();
        } finally {
          await transport.close();
        }
      }
    })();
    return disposal;
  };
  const onAbort = () => {
    dispose().catch(reportError);
  };
  signal.addEventListener(ABORT_EVENT, onAbort, { once: true });
  try {
    await bridge.connect(transport);
    signal.throwIfAborted();
    iframe.setAttribute("sandbox", OUTER_SANDBOX_PERMISSIONS);
    iframe.src = sandbox.href;
  } catch (error) {
    await dispose();
    throw error;
  }
  return {
    dispose,
    // @spec MCA-005 — The official context update preserves non-locale fields.
    updateLocale: (locale) => {
      if (disposed || signal.aborted) return;
      bridge.setHostContext({
        ...hostContext,
        locale: locale || DEFAULT_APP_LOCALE,
      });
    },
  };
}
