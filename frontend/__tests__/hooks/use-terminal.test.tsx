import { beforeAll, describe, expect, it, vi, afterEach } from "vitest";
import { useTerminal } from "#/hooks/use-terminal";
import { Command, useCommandStore } from "#/state/command-store";
import { renderWithProviders } from "../../test-utils";

// Mock the WsClient context
vi.mock("#/context/ws-client-provider", () => ({
  useWsClient: () => ({
    send: vi.fn(),
    status: "CONNECTED",
    isLoadingMessages: false,
    events: [],
  }),
}));

// Mock useActiveConversation
vi.mock("#/hooks/query/use-active-conversation", () => ({
  useActiveConversation: () => ({
    data: {
      id: "test-conversation-id",
      conversation_version: "V0",
    },
    isFetched: true,
  }),
}));

// Mock useConversationWebSocket (returns null for V0 conversations)
vi.mock("#/contexts/conversation-websocket-context", () => ({
  useConversationWebSocket: () => null,
}));

function TestTerminalComponent() {
  const ref = useTerminal();
  return <div ref={ref} />;
}

describe("useTerminal", () => {
  const mockTerminal = vi.hoisted(() => ({
    loadAddon: vi.fn(),
    open: vi.fn(),
    write: vi.fn(),
    writeln: vi.fn(),
    onKey: vi.fn(),
    attachCustomKeyEventHandler: vi.fn(),
    dispose: vi.fn(),
  }));

  beforeAll(() => {
    // mock ResizeObserver
    window.ResizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }));

    // mock Terminal
    vi.mock("@xterm/xterm", async (importOriginal) => ({
      ...(await importOriginal<typeof import("@xterm/xterm")>()),
      Terminal: vi.fn().mockImplementation(() => mockTerminal),
    }));
  });

  afterEach(() => {
    vi.clearAllMocks();
    // Reset command store between tests
    useCommandStore.setState({ commands: [] });
  });

  it("should render", () => {
    renderWithProviders(<TestTerminalComponent />);
  });

  it("should render the commands in the terminal", () => {
    const commands: Command[] = [
      { content: "echo hello", type: "input" },
      { content: "hello", type: "output" },
    ];

    // Set commands in store before rendering to ensure they're picked up during initialization
    useCommandStore.setState({ commands });

    renderWithProviders(<TestTerminalComponent />);

    expect(mockTerminal.writeln).toHaveBeenNthCalledWith(1, "echo hello");
    expect(mockTerminal.writeln).toHaveBeenNthCalledWith(2, "hello");
  });
});
