import { beforeAll, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { afterEach } from "node:test";
import { ReactNode } from "react";
import { useTerminal } from "#/hooks/use-terminal";
import { Command } from "#/state/command-slice";

interface TestTerminalComponentProps {
  commands: Command[];
}

function TestTerminalComponent({
  commands,
}: TestTerminalComponentProps) {
  const ref = useTerminal({ commands });
  return <div ref={ref} />;
}

interface WrapperProps {
  children: ReactNode;
}

function Wrapper({ children }: WrapperProps) {
  return <div>{children}</div>;
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
    render(<TestTerminalComponent commands={[]} />, {
      wrapper: Wrapper,
    });
  });

  it("should render the commands in the terminal", () => {
    const commands: Command[] = [
      { content: "echo hello", type: "input" },
      { content: "hello", type: "output" },
    ];

    render(<TestTerminalComponent commands={commands} />, {
      wrapper: Wrapper,
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

    render(
      <TestTerminalComponent
        commands={commands}
      />,
      {
        wrapper: Wrapper,
      },
    );

    // This test is no longer relevant as secrets filtering has been removed
  });
});
