import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ObservationEvent } from "#/types/agent-server/core";
import type { MCPToolObservation } from "#/types/agent-server/core/base/observation";
import type {
  MCPAppDescriptor,
  MCPAppHost,
  MCPAppScope,
  MCPAppSession,
} from "#/types/mcp-app";
import { MCPAppArtifact } from "./mcp-app-artifact";
import { MCPAppHostProvider } from "./mcp-app-host-context";

const bridgeMocks = vi.hoisted(() => ({
  mount: vi.fn(),
}));

vi.mock("./mcp-app-bridge", () => ({
  mountMCPAppBridge: bridgeMocks.mount,
}));

const event = {
  id: "result-1",
  timestamp: "2026-10-13T00:00:00Z",
  source: "environment",
  tool_name: "show_chart",
  tool_call_id: "call-1",
  action_id: "action-1",
  observation: {
    kind: "MCPToolObservation",
    tool_name: "show_chart",
    content: [{ type: "text", text: "Chart ready" }],
    is_error: false,
  },
} satisfies ObservationEvent<MCPToolObservation>;

const descriptor: MCPAppDescriptor = {
  resourceUri: "ui://chart/view",
  tool: {
    name: "show_chart",
    _meta: { ui: { resourceUri: "ui://chart/view" } },
  },
  toolInput: { symbol: "OPEN" },
  toolResult: { content: [{ type: "text", text: "Chart ready" }] },
};

const scope: MCPAppScope = {
  backendId: "local-backend",
  orgId: null,
  connectionRevision: 2,
  conversationId: "conversation-main",
  planningConversationId: "conversation-plan",
  writableConversationId: "conversation-main",
};

function renderArtifact(host: MCPAppHost | null, currentScope = scope) {
  return render(
    <MCPAppHostProvider host={host} scope={currentScope}>
      <MCPAppArtifact event={event} descriptor={descriptor} />
    </MCPAppHostProvider>,
  );
}

function createHost(readResource = vi.fn(async () => ({ contents: [] }))) {
  const session: MCPAppSession = { readResource, dispose: vi.fn() };
  const host: MCPAppHost = {
    sandboxUrl: "https://sandbox.example.com/sandbox.html",
    open: vi.fn(async () => session),
  };
  return { host, session };
}

beforeEach(() => {
  bridgeMocks.mount.mockReset();
  bridgeMocks.mount.mockImplementation(async (options) => {
    options.onReady();
    return { dispose: vi.fn(async () => undefined) };
  });
});

// @spec MCA-004 — Views open only through an explicit, conversation-bound Host
describe("MCPAppArtifact", () => {
  it("keeps the artifact unavailable when no trusted Host is installed", () => {
    renderArtifact(null);

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(bridgeMocks.mount).not.toHaveBeenCalled();
  });

  it("binds the originating call and does not retarget writes after a mode switch", async () => {
    const { host, session } = createHost();
    const view = renderArtifact(host);

    await waitFor(() => expect(host.open).toHaveBeenCalledOnce());
    await waitFor(() => expect(bridgeMocks.mount).toHaveBeenCalledOnce());
    expect(host.open).toHaveBeenCalledWith(
      {
        backendId: "local-backend",
        orgId: null,
        connectionRevision: 2,
        ownerConversationId: "conversation-main",
        eventId: "result-1",
        actionId: "action-1",
        toolCallId: "call-1",
        toolName: "show_chart",
        resourceUri: "ui://chart/view",
      },
      { signal: expect.any(AbortSignal) },
    );

    const bridgeOptions = bridgeMocks.mount.mock.calls[0][0];
    expect(bridgeOptions.isWritable()).toBe(true);
    view.rerender(
      <MCPAppHostProvider
        host={host}
        scope={{ ...scope, writableConversationId: "conversation-plan" }}
      >
        <MCPAppArtifact event={event} descriptor={descriptor} />
      </MCPAppHostProvider>,
    );

    expect(host.open).toHaveBeenCalledOnce();
    expect(bridgeOptions.isWritable()).toBe(false);
    view.unmount();
    await waitFor(() => expect(session.dispose).toHaveBeenCalledOnce());
  });

  it("disposes a failed session and retries with a fresh binding", async () => {
    const readResource = vi
      .fn()
      .mockRejectedValueOnce(new Error("resource unavailable"))
      .mockResolvedValueOnce({ contents: [] });
    const { host, session } = createHost(readResource);
    renderArtifact(host);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(session.dispose).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => expect(host.open).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(bridgeMocks.mount).toHaveBeenCalledOnce());
  });

  it("closes the session when bridge initialization fails", async () => {
    const bridgeDispose = vi.fn(async () => undefined);
    bridgeMocks.mount.mockImplementationOnce(async (options) => {
      options.iframe.setAttribute("src", options.sandboxUrl);
      options.onError(new Error("invalid handshake"));
      return { dispose: bridgeDispose };
    });
    const { host, session } = createHost();
    renderArtifact(host);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(document.querySelector("iframe")).not.toHaveAttribute("src");
    await waitFor(() => expect(session.dispose).toHaveBeenCalledOnce());
    await waitFor(() => expect(bridgeDispose).toHaveBeenCalledOnce());
  });
});
