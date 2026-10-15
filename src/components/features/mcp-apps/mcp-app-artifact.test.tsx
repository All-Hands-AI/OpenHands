import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createInstance, type i18n } from "i18next";
import { I18nextProvider } from "react-i18next";
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

vi.unmock("react-i18next");

let language: i18n;

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

function artifactView(host: MCPAppHost | null, currentScope = scope) {
  return (
    <I18nextProvider i18n={language}>
      <MCPAppHostProvider host={host} scope={currentScope}>
        <MCPAppArtifact event={event} descriptor={descriptor} />
      </MCPAppHostProvider>
    </I18nextProvider>
  );
}

function renderArtifact(host: MCPAppHost | null, currentScope = scope) {
  return render(artifactView(host, currentScope));
}

function createHost(readResource = vi.fn(async () => ({ contents: [] }))) {
  const session: MCPAppSession = { readResource, dispose: vi.fn() };
  const host: MCPAppHost = {
    sandboxUrl: "https://sandbox.example.com/sandbox.html",
    open: vi.fn(async () => session),
  };
  return { host, session };
}

beforeEach(async () => {
  language = createInstance();
  await language.init({
    lng: "en",
    fallbackLng: "en",
    defaultNS: "openhands",
    resources: {
      en: { openhands: { MCP$APP_TITLE: "Interactive App" } },
      ja: { openhands: { MCP$APP_TITLE: "App in Japanese" } },
      ar: { openhands: { MCP$APP_TITLE: "App in Arabic" } },
    },
  });
  bridgeMocks.mount.mockReset();
  bridgeMocks.mount.mockImplementation(async (options) => {
    options.onReady();
    return {
      dispose: vi.fn(async () => undefined),
      updateLocale: vi.fn(),
    };
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
      artifactView(host, {
        ...scope,
        writableConversationId: "conversation-plan",
      }),
    );

    expect(host.open).toHaveBeenCalledOnce();
    expect(bridgeOptions.isWritable()).toBe(false);
    view.unmount();
    await waitFor(() => expect(session.dispose).toHaveBeenCalledOnce());
  });

  // @spec MCA-005 — Language changes update the active View without reopening it.
  it("uses the resolved UI locale and updates the existing bridge when language changes", async () => {
    await language.changeLanguage("ja-JP");
    const { host, session } = createHost();
    const view = renderArtifact(host);
    await waitFor(() => expect(bridgeMocks.mount).toHaveBeenCalledOnce());
    const options = bridgeMocks.mount.mock.calls[0][0];
    expect(options.locale).toBe("ja");
    const mounted = await bridgeMocks.mount.mock.results[0].value;
    const iframe = screen.getByTitle("App in Japanese");

    await act(() => language.changeLanguage("ar"));

    expect(mounted.updateLocale).toHaveBeenLastCalledWith("ar");
    expect(screen.getByTitle("App in Arabic")).toBe(iframe);
    expect(host.open).toHaveBeenCalledOnce();
    expect(session.readResource).toHaveBeenCalledOnce();
    expect(bridgeMocks.mount).toHaveBeenCalledOnce();
    view.unmount();
    mounted.updateLocale.mockClear();
    await act(() => language.changeLanguage("en"));
    expect(mounted.updateLocale).not.toHaveBeenCalled();
  });

  it("keeps the latest locale across pending resource reads and bridge connection", async () => {
    let finishRead: ((resource: { contents: [] }) => void) | undefined;
    const { host } = createHost(
      vi.fn(
        () =>
          new Promise((resolve) => {
            finishRead = resolve;
          }),
      ),
    );
    const mounted = {
      dispose: vi.fn(async () => undefined),
      updateLocale: vi.fn(),
    };
    let finishMount: (() => void) | undefined;
    bridgeMocks.mount.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finishMount = () => resolve(mounted);
        }),
    );
    renderArtifact(host);
    await waitFor(() => expect(finishRead).toBeDefined());
    await act(() => language.changeLanguage("ja"));
    await act(async () => finishRead?.({ contents: [] }));
    await waitFor(() => expect(bridgeMocks.mount).toHaveBeenCalledOnce());
    expect(bridgeMocks.mount.mock.calls[0][0].locale).toBe("ja");
    await act(() => language.changeLanguage("ar"));
    await act(async () => finishMount?.());
    expect(mounted.updateLocale).toHaveBeenLastCalledWith("ar");
    expect(host.open).toHaveBeenCalledOnce();
  });

  it("disposes an abandoned pending bridge without updating its locale", async () => {
    const { host } = createHost();
    const mounted = {
      dispose: vi.fn(async () => undefined),
      updateLocale: vi.fn(),
    };
    let finishMount: (() => void) | undefined;
    bridgeMocks.mount.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finishMount = () => resolve(mounted);
        }),
    );
    const view = renderArtifact(host);
    await waitFor(() => expect(finishMount).toBeDefined());
    view.unmount();
    await act(() => language.changeLanguage("ar"));
    await act(async () => finishMount?.());
    expect(mounted.dispose).toHaveBeenCalledOnce();
    expect(mounted.updateLocale).not.toHaveBeenCalled();
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
      return { dispose: bridgeDispose, updateLocale: vi.fn() };
    });
    const { host, session } = createHost();
    renderArtifact(host);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(document.querySelector("iframe")).not.toHaveAttribute("src");
    await waitFor(() => expect(session.dispose).toHaveBeenCalledOnce());
    await waitFor(() => expect(bridgeDispose).toHaveBeenCalledOnce());
  });
});
