import { beforeAll, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { afterEach } from "node:test";
import { ReactNode } from "react";
import { useTerminal } from "#/hooks/use-terminal";
import { Command } from "#/state/command-slice";

interface TestTerminalComponentProps {
  commands: Command[];
  secrets: string[];
}

function TestTerminalComponent({
  commands,
  secrets,
}: TestTerminalComponentProps) {
  const ref = useTerminal({ commands, secrets, disabled: false });
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
    render(<TestTerminalComponent commands={[]} secrets={[]} />, {
      wrapper: Wrapper,
    });
  });

  it("should render the commands in the terminal", () => {
    const commands: Command[] = [
      { content: "echo hello", type: "input" },
      { content: "hello", type: "output" },
    ];

    render(<TestTerminalComponent commands={commands} secrets={[]} />, {
      wrapper: Wrapper,
    });

    // Input commands should be displayed
    expect(mockTerminal.writeln).toHaveBeenCalledWith("echo hello");
    // Output commands should be displayed
    expect(mockTerminal.writeln).toHaveBeenCalledWith("hello");
  });

  it("should hide secrets in the terminal", () => {
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
        secrets={[secret, anotherSecret]}
      />,
      {
        wrapper: Wrapper,
      },
    );

    // Input command should be displayed with secrets masked
    expect(mockTerminal.writeln).toHaveBeenCalledWith(
      `export GITHUB_TOKEN=${"*".repeat(10)},${"*".repeat(10)},${"*".repeat(10)}`,
    );
    
    // Output command should be displayed with secrets masked
    expect(mockTerminal.writeln).toHaveBeenCalledWith("*".repeat(10));
  });
  
  it("should prevent duplicate command display", () => {
    const inputCommand = "ls -la";
    const commands: Command[] = [
      { content: inputCommand, type: "input" },
      { content: `${inputCommand}\nfile1.txt\nfile2.txt`, type: "output" },
    ];

    render(<TestTerminalComponent commands={commands} secrets={[]} />, {
      wrapper: Wrapper,
    });

    // Input command should be displayed
    expect(mockTerminal.writeln).toHaveBeenCalledWith(inputCommand);
    
    // Output should not be displayed since it starts with the input command
    // This prevents the duplicate display of the command
    expect(mockTerminal.writeln).not.toHaveBeenCalledWith(`${inputCommand}\nfile1.txt\nfile2.txt`);
  });
});
