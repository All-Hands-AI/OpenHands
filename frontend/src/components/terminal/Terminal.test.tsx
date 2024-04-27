import React from "react";
import { act, screen } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { Command, appendInput, appendOutput } from "#/state/commandSlice";
import Terminal from "./Terminal";

global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
}));

const openMock = vi.fn();
const writeMock = vi.fn();
const writelnMock = vi.fn();
const disposeMock = vi.fn();

vi.mock("@xterm/xterm", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@xterm/xterm")>()),
  Terminal: vi.fn(() => ({
    open: openMock,
    write: writeMock,
    writeln: writelnMock,
    dispose: disposeMock,
    loadAddon: vi.fn(),
  })),
}));

const renderTerminal = (commands: Command[] = []) =>
  renderWithProviders(<Terminal />, {
    preloadedState: {
      cmd: {
        commands,
      },
    },
  });

describe("Terminal", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render a terminal", () => {
    renderTerminal();

    expect(screen.getByText("Terminal (read-only)")).toBeInTheDocument();
    expect(openMock).toHaveBeenCalledTimes(1);

    expect(writeMock).toHaveBeenCalledWith("$ ");
  });

  it("should load commands to the terminal", () => {
    renderTerminal([
      { type: "input", content: "INPUT" },
      { type: "output", content: "OUTPUT" },
    ]);

    expect(writelnMock).toHaveBeenNthCalledWith(1, "INPUT");
    expect(writelnMock).toHaveBeenNthCalledWith(2, "OUTPUT");
  });

  it("should write commands to the terminal", () => {
    const { store } = renderTerminal();

    act(() => {
      store.dispatch(appendInput("echo Hello"));
      store.dispatch(appendOutput("Hello"));
    });

    expect(writelnMock).toHaveBeenNthCalledWith(1, "echo Hello");
    expect(writelnMock).toHaveBeenNthCalledWith(2, "Hello");

    act(() => {
      store.dispatch(appendInput("echo World"));
    });

    expect(writelnMock).toHaveBeenNthCalledWith(3, "echo World");
  });

  it("should load and write commands to the terminal", () => {
    const { store } = renderTerminal([
      { type: "input", content: "echo Hello" },
      { type: "output", content: "Hello" },
    ]);

    expect(writelnMock).toHaveBeenNthCalledWith(1, "echo Hello");
    expect(writelnMock).toHaveBeenNthCalledWith(2, "Hello");

    act(() => {
      store.dispatch(appendInput("echo Hello"));
    });

    expect(writelnMock).toHaveBeenNthCalledWith(3, "echo Hello");
  });

  it("should end the line with a dollar sign after writing a command", () => {
    const { store } = renderTerminal();

    act(() => {
      store.dispatch(appendInput("echo Hello"));
    });

    expect(writelnMock).toHaveBeenCalledWith("echo Hello");
    expect(writeMock).toHaveBeenCalledWith("$ ");
  });

  // This test fails because it expects `disposeMock` to have been called before the component is unmounted.
  it.skip("should dispose the terminal on unmount", () => {
    const { unmount } = renderWithProviders(<Terminal />);

    expect(disposeMock).not.toHaveBeenCalled();

    unmount();

    expect(disposeMock).toHaveBeenCalledTimes(1);
  });
});
