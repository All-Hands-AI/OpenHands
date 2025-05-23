import { beforeAll, describe, expect, it, vi } from "vitest";
import { afterEach } from "node:test";
import { useTerminal } from "#/hooks/use-terminal";
import { Command } from "#/state/command-slice";
import { AgentState } from "#/types/agent-state";
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

interface TestTerminalComponentProps {
  commands: Command[];
}

function TestTerminalComponent({
  commands,
}: TestTerminalComponentProps) {
  const ref = useTerminal({ commands });
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
  });

  it("should render", () => {
    renderWithProviders(<TestTerminalComponent commands={[]} />, {
      preloadedState: {
        agent: { curAgentState: AgentState.RUNNING },
        cmd: { commands: [] },
      },
    });
  });

  it("should render the commands in the terminal", () => {
    const commands: Command[] = [
      { content: "echo hello", type: "input" },
      { content: "hello", type: "output" },
    ];

    renderWithProviders(<TestTerminalComponent commands={commands} />, {
      preloadedState: {
        agent: { curAgentState: AgentState.RUNNING },
        cmd: { commands },
      },
    });

    expect(mockTerminal.writeln).toHaveBeenNthCalledWith(1, "echo hello");
    expect(mockTerminal.writeln).toHaveBeenNthCalledWith(2, "hello");
  });

  // This test is no longer relevant as secrets filtering has been removed
  it.skip("should hide secrets in the terminal", () => {
    const secret = "super_secret_github_token";
    const anotherSecret = "super_secret_another_token";
    const commands: Command[] = [
      {
        content: `export GITHUB_TOKEN=${secret},${anotherSecret},${secret}`,
        type: "input",
      },
      { content: secret, type: "output" },
    ];

    renderWithProviders(
      <TestTerminalComponent
        commands={commands}
      />,
      {
        preloadedState: {
          agent: { curAgentState: AgentState.RUNNING },
          cmd: { commands },
        },
      },
    );

    // This test is no longer relevant as secrets filtering has been removed
  });
});
