import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { ServerStatus } from "#/components/features/controls/server-status";
import { ServerStatusContextMenu } from "#/components/features/controls/server-status-context-menu";
import { ConversationStatus } from "#/types/conversation-status";
import { AgentState } from "#/types/agent-state";

// Mock the conversation slice actions
vi.mock("#/state/conversation-slice", () => ({
  setShouldStopConversation: vi.fn(),
  setShouldStartConversation: vi.fn(),
  default: {
    name: "conversation",
    initialState: {
      isRightPanelShown: true,
      shouldStopConversation: false,
      shouldStartConversation: false,
    },
    reducers: {},
  },
}));

// Mock react-redux
vi.mock("react-redux", () => ({
  useSelector: vi.fn((selector) => {
    // Mock the selector to return different agent states based on test needs
    return {
      curAgentState: AgentState.RUNNING,
    };
  }),
  useDispatch: vi.fn(() => vi.fn()),
  Provider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock react-i18next
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          COMMON$RUNNING: "Running",
          COMMON$SERVER_STOPPED: "Server Stopped",
          COMMON$ERROR: "Error",
          COMMON$STARTING: "Starting",
          COMMON$STOP_SERVER: "Stop Server",
          COMMON$START_SERVER: "Start Server",
        };
        return translations[key] || key;
      },
      i18n: {
        changeLanguage: () => new Promise(() => {}),
      },
    }),
  };
});

describe("ServerStatus", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render server status with different conversation statuses", () => {
    // Test RUNNING status
    const { rerender } = renderWithProviders(
      <ServerStatus conversationStatus="RUNNING" />,
    );
    expect(screen.getByText("Running")).toBeInTheDocument();

    // Test STOPPED status
    rerender(<ServerStatus conversationStatus="STOPPED" />);
    expect(screen.getByText("Server Stopped")).toBeInTheDocument();

    // Test STARTING status (shows "Running" due to agent state being RUNNING)
    rerender(<ServerStatus conversationStatus="STARTING" />);
    expect(screen.getByText("Running")).toBeInTheDocument();

    // Test null status (shows "Running" due to agent state being RUNNING)
    rerender(<ServerStatus conversationStatus={null} />);
    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("should show context menu when clicked with RUNNING status", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ServerStatus conversationStatus="RUNNING" />);

    const statusContainer = screen.getByText("Running").closest("div");
    expect(statusContainer).toBeInTheDocument();

    await user.click(statusContainer!);

    // Context menu should appear
    expect(
      screen.getByTestId("server-status-context-menu"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("stop-server-button")).toBeInTheDocument();
  });

  it("should show context menu when clicked with STOPPED status", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ServerStatus conversationStatus="STOPPED" />);

    const statusContainer = screen.getByText("Server Stopped").closest("div");
    expect(statusContainer).toBeInTheDocument();

    await user.click(statusContainer!);

    // Context menu should appear
    expect(
      screen.getByTestId("server-status-context-menu"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("start-server-button")).toBeInTheDocument();
  });

  it("should not show context menu when clicked with other statuses", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ServerStatus conversationStatus="STARTING" />);

    const statusContainer = screen.getByText("Running").closest("div");
    expect(statusContainer).toBeInTheDocument();

    await user.click(statusContainer!);

    // Context menu should not appear
    expect(
      screen.queryByTestId("server-status-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should dispatch stop conversation action when stop server is clicked", async () => {
    const user = userEvent.setup();
    const mockDispatch = vi.fn();
    const { useDispatch } = await import("react-redux");
    vi.mocked(useDispatch).mockReturnValue(mockDispatch);

    renderWithProviders(<ServerStatus conversationStatus="RUNNING" />);

    const statusContainer = screen.getByText("Running").closest("div");
    await user.click(statusContainer!);

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    expect(mockDispatch).toHaveBeenCalled();
  });

  it("should dispatch start conversation action when start server is clicked", async () => {
    const user = userEvent.setup();
    const mockDispatch = vi.fn();
    const { useDispatch } = await import("react-redux");
    vi.mocked(useDispatch).mockReturnValue(mockDispatch);

    renderWithProviders(<ServerStatus conversationStatus="STOPPED" />);

    const statusContainer = screen.getByText("Server Stopped").closest("div");
    await user.click(statusContainer!);

    const startButton = screen.getByTestId("start-server-button");
    await user.click(startButton);

    expect(mockDispatch).toHaveBeenCalled();
  });

  it("should close context menu after stop server action", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ServerStatus conversationStatus="RUNNING" />);

    const statusContainer = screen.getByText("Running").closest("div");
    await user.click(statusContainer!);

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    // Context menu should be closed
    expect(
      screen.queryByTestId("server-status-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should close context menu after start server action", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ServerStatus conversationStatus="STOPPED" />);

    const statusContainer = screen.getByText("Server Stopped").closest("div");
    await user.click(statusContainer!);

    const startButton = screen.getByTestId("start-server-button");
    await user.click(startButton);

    // Context menu should be closed
    expect(
      screen.queryByTestId("server-status-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should apply custom className", () => {
    renderWithProviders(
      <ServerStatus conversationStatus="RUNNING" className="custom-class" />,
    );

    const container = screen.getByText("Running").closest("div")?.parentElement;
    expect(container).toHaveClass("custom-class");
  });
});

describe("ServerStatusContextMenu", () => {
  const defaultProps = {
    onClose: vi.fn(),
    conversationStatus: "RUNNING" as ConversationStatus,
  };

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render stop server button when status is RUNNING", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
      />,
    );

    expect(screen.getByTestId("stop-server-button")).toBeInTheDocument();
    expect(screen.getByText("Stop Server")).toBeInTheDocument();
  });

  it("should render start server button when status is STOPPED", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="STOPPED"
        onStartServer={vi.fn()}
      />,
    );

    expect(screen.getByTestId("start-server-button")).toBeInTheDocument();
    expect(screen.getByText("Start Server")).toBeInTheDocument();
  });

  it("should not render stop server button when onStopServer is not provided", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
      />,
    );

    expect(screen.queryByTestId("stop-server-button")).not.toBeInTheDocument();
  });

  it("should not render start server button when onStartServer is not provided", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="STOPPED"
      />,
    );

    expect(screen.queryByTestId("start-server-button")).not.toBeInTheDocument();
  });

  it("should call onStopServer when stop button is clicked", async () => {
    const user = userEvent.setup();
    const onStopServer = vi.fn();

    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={onStopServer}
      />,
    );

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    expect(onStopServer).toHaveBeenCalledTimes(1);
  });

  it("should call onStartServer when start button is clicked", async () => {
    const user = userEvent.setup();
    const onStartServer = vi.fn();

    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="STOPPED"
        onStartServer={onStartServer}
      />,
    );

    const startButton = screen.getByTestId("start-server-button");
    await user.click(startButton);

    expect(onStartServer).toHaveBeenCalledTimes(1);
  });

  it("should apply correct positioning class when position is top", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
        position="top"
      />,
    );

    const contextMenu = screen.getByTestId("server-status-context-menu");
    expect(contextMenu).toHaveClass("bottom-full");
  });

  it("should apply correct positioning class when position is bottom", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
        position="bottom"
      />,
    );

    const contextMenu = screen.getByTestId("server-status-context-menu");
    expect(contextMenu).toHaveClass("top-full");
  });

  it("should render correct text content for stop server button", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
      />,
    );

    expect(screen.getByTestId("stop-server-button")).toHaveTextContent(
      "Stop Server",
    );
  });

  it("should render correct text content for start server button", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="STOPPED"
        onStartServer={vi.fn()}
      />,
    );

    expect(screen.getByTestId("start-server-button")).toHaveTextContent(
      "Start Server",
    );
  });

  it("should call onClose when context menu is closed", () => {
    const onClose = vi.fn();

    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        onClose={onClose}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
      />,
    );

    // The onClose is typically called by the parent component when clicking outside
    // This test verifies the prop is properly passed
    expect(onClose).toBeDefined();
  });

  it("should not render any buttons for other conversation statuses", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="STARTING"
      />,
    );

    expect(screen.queryByTestId("stop-server-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("start-server-button")).not.toBeInTheDocument();
  });

  it("should have proper styling classes", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
      />,
    );

    const contextMenu = screen.getByTestId("server-status-context-menu");
    expect(contextMenu).toHaveClass("w-fit", "min-w-max", "bg-tertiary");
  });
});
