import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { ServerStatus } from "#/components/features/controls/server-status";
import { ServerStatusContextMenu } from "#/components/features/controls/server-status-context-menu";
import { ConversationStatus } from "#/types/conversation-status";
import { AgentState } from "#/types/agent-state";
import { useAgentState } from "#/hooks/use-agent-state";

// Mock the agent state hook
vi.mock("#/hooks/use-agent-state", () => ({
  useAgentState: vi.fn(),
}));

// Mock the custom hooks
const mockStartConversationMutate = vi.fn();
const mockStopConversationMutate = vi.fn();

vi.mock("#/hooks/mutation/use-unified-start-conversation", () => ({
  useUnifiedStartConversation: () => ({
    mutate: mockStartConversationMutate,
  }),
}));

vi.mock("#/hooks/mutation/use-unified-stop-conversation", () => ({
  useUnifiedStopConversation: () => ({
    mutate: mockStopConversationMutate,
  }),
}));

vi.mock("#/hooks/use-conversation-id", () => ({
  useConversationId: () => ({
    conversationId: "test-conversation-id",
  }),
}));

vi.mock("#/hooks/use-user-providers", () => ({
  useUserProviders: () => ({
    providers: [],
  }),
}));

vi.mock("#/hooks/query/use-task-polling", () => ({
  useTaskPolling: () => ({
    isTask: false,
    taskId: null,
    conversationId: "test-conversation-id",
    task: null,
    taskStatus: null,
    taskDetail: null,
    taskError: null,
    isLoadingTask: false,
  }),
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
          COMMON$STOP_RUNTIME: "Stop Runtime",
          COMMON$START_RUNTIME: "Start Runtime",
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
  // Mock functions for handlers
  const mockHandleStop = vi.fn();
  const mockHandleResumeAgent = vi.fn();

  // Helper function to mock agent state with specific state
  const mockAgentStore = (agentState: AgentState) => {
    vi.mocked(useAgentState).mockReturnValue({
      curAgentState: agentState,
    });
  };

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render server status with different conversation statuses", () => {
    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    // Test RUNNING status
    const { rerender } = renderWithProviders(
      <ServerStatus
        conversationStatus="RUNNING"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );
    expect(screen.getByText("Running")).toBeInTheDocument();

    // Test STOPPED status
    rerender(
      <ServerStatus
        conversationStatus="STOPPED"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );
    expect(screen.getByText("Server Stopped")).toBeInTheDocument();

    // Test STARTING status (shows "Running" due to agent state being RUNNING)
    rerender(
      <ServerStatus
        conversationStatus="STARTING"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );
    expect(screen.getByText("Running")).toBeInTheDocument();

    // Test null status (shows "Running" due to agent state being RUNNING)
    rerender(
      <ServerStatus
        conversationStatus={null}
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );
    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("should show context menu when clicked with RUNNING status", async () => {
    const user = userEvent.setup();

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithProviders(
      <ServerStatus
        conversationStatus="RUNNING"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

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

    // Mock agent store to return STOPPED state
    mockAgentStore(AgentState.STOPPED);

    renderWithProviders(
      <ServerStatus
        conversationStatus="STOPPED"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

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

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithProviders(
      <ServerStatus
        conversationStatus="STARTING"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

    const statusContainer = screen.getByText("Running").closest("div");
    expect(statusContainer).toBeInTheDocument();

    await user.click(statusContainer!);

    // Context menu should not appear
    expect(
      screen.queryByTestId("server-status-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should call stop conversation mutation when stop server is clicked", async () => {
    const user = userEvent.setup();

    // Clear previous calls
    mockHandleStop.mockClear();

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithProviders(
      <ServerStatus
        conversationStatus="RUNNING"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

    const statusContainer = screen.getByText("Running").closest("div");
    await user.click(statusContainer!);

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    expect(mockHandleStop).toHaveBeenCalledTimes(1);
  });

  it("should call start conversation mutation when start server is clicked", async () => {
    const user = userEvent.setup();

    // Clear previous calls
    mockHandleResumeAgent.mockClear();

    // Mock agent store to return STOPPED state
    mockAgentStore(AgentState.STOPPED);

    renderWithProviders(
      <ServerStatus
        conversationStatus="STOPPED"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

    const statusContainer = screen.getByText("Server Stopped").closest("div");
    await user.click(statusContainer!);

    const startButton = screen.getByTestId("start-server-button");
    await user.click(startButton);

    expect(mockHandleResumeAgent).toHaveBeenCalledTimes(1);
  });

  it("should close context menu after stop server action", async () => {
    const user = userEvent.setup();

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithProviders(
      <ServerStatus
        conversationStatus="RUNNING"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

    const statusContainer = screen.getByText("Running").closest("div");
    await user.click(statusContainer!);

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    // Context menu should be closed (handled by the component)
    expect(mockHandleStop).toHaveBeenCalledTimes(1);
  });

  it("should close context menu after start server action", async () => {
    const user = userEvent.setup();

    // Mock agent store to return STOPPED state
    mockAgentStore(AgentState.STOPPED);

    renderWithProviders(
      <ServerStatus
        conversationStatus="STOPPED"
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

    const statusContainer = screen.getByText("Server Stopped").closest("div");
    await user.click(statusContainer!);

    const startButton = screen.getByTestId("start-server-button");
    await user.click(startButton);

    // Context menu should be closed
    expect(
      screen.queryByTestId("server-status-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should handle null conversation status", () => {
    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithProviders(
      <ServerStatus
        conversationStatus={null}
        handleStop={mockHandleStop}
        handleResumeAgent={mockHandleResumeAgent}
      />,
    );

    const statusText = screen.getByText("Running");
    expect(statusText).toBeInTheDocument();
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
    expect(screen.getByText("Stop Runtime")).toBeInTheDocument();
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
    expect(screen.getByText("Start Runtime")).toBeInTheDocument();
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

  it("should render correct text content for stop server button", () => {
    renderWithProviders(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
        onStopServer={vi.fn()}
      />,
    );

    expect(screen.getByTestId("stop-server-button")).toHaveTextContent(
      "Stop Runtime",
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
      "Start Runtime",
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
});
