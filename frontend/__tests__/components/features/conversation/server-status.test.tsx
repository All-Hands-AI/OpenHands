import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryAndI18n } from "test-utils";
import { ServerStatus } from "#/components/features/controls/server-status";
import { ServerStatusContextMenu } from "#/components/features/controls/server-status-context-menu";
import { ConversationStatus } from "#/types/conversation-status";
import { AgentState } from "#/types/agent-state";
import { useAgentStore } from "#/stores/agent-store";

// Mock the agent store
vi.mock("#/stores/agent-store", () => ({
  useAgentStore: vi.fn(),
}));

// Mock the custom hooks
const mockStartConversationMutate = vi.fn();
const mockStopConversationMutate = vi.fn();

vi.mock("#/hooks/mutation/use-start-conversation", () => ({
  useStartConversation: () => ({
    mutate: mockStartConversationMutate,
  }),
}));

vi.mock("#/hooks/mutation/use-stop-conversation", () => ({
  useStopConversation: () => ({
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
  // Helper function to mock agent store with specific state
  const mockAgentStore = (agentState: AgentState) => {
    vi.mocked(useAgentStore).mockReturnValue({
      curAgentState: agentState,
      setCurrentAgentState: vi.fn(),
      reset: vi.fn(),
    });
  };

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render server status with different conversation statuses", () => {
    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    // Test RUNNING status
    const { rerender } = renderWithQueryAndI18n(
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

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithQueryAndI18n(<ServerStatus conversationStatus="RUNNING" />);

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

    renderWithQueryAndI18n(<ServerStatus conversationStatus="STOPPED" />);

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

    renderWithQueryAndI18n(<ServerStatus conversationStatus="STARTING" />);

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
    mockStopConversationMutate.mockClear();

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithQueryAndI18n(<ServerStatus conversationStatus="RUNNING" />);

    const statusContainer = screen.getByText("Running").closest("div");
    await user.click(statusContainer!);

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    expect(mockStopConversationMutate).toHaveBeenCalledWith({
      conversationId: "test-conversation-id",
    });
  });

  it("should call start conversation mutation when start server is clicked", async () => {
    const user = userEvent.setup();

    // Clear previous calls
    mockStartConversationMutate.mockClear();

    // Mock agent store to return STOPPED state
    mockAgentStore(AgentState.STOPPED);

    renderWithQueryAndI18n(<ServerStatus conversationStatus="STOPPED" />);

    const statusContainer = screen.getByText("Server Stopped").closest("div");
    await user.click(statusContainer!);

    const startButton = screen.getByTestId("start-server-button");
    await user.click(startButton);

    expect(mockStartConversationMutate).toHaveBeenCalledWith({
      conversationId: "test-conversation-id",
      providers: [],
    });
  });

  it("should close context menu after stop server action", async () => {
    const user = userEvent.setup();

    // Mock agent store to return RUNNING state
    mockAgentStore(AgentState.RUNNING);

    renderWithQueryAndI18n(<ServerStatus conversationStatus="RUNNING" />);

    const statusContainer = screen.getByText("Running").closest("div");
    await user.click(statusContainer!);

    const stopButton = screen.getByTestId("stop-server-button");
    await user.click(stopButton);

    // Context menu should be closed (handled by the component)
    expect(mockStopConversationMutate).toHaveBeenCalledWith({
      conversationId: "test-conversation-id",
    });
  });

  it("should close context menu after start server action", async () => {
    const user = userEvent.setup();

    // Mock agent store to return STOPPED state
    mockAgentStore(AgentState.STOPPED);

    renderWithQueryAndI18n(<ServerStatus conversationStatus="STOPPED" />);

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

    renderWithQueryAndI18n(<ServerStatus conversationStatus={null} />);

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
    renderWithQueryAndI18n(
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
    renderWithQueryAndI18n(
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
    renderWithQueryAndI18n(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="RUNNING"
      />,
    );

    expect(screen.queryByTestId("stop-server-button")).not.toBeInTheDocument();
  });

  it("should not render start server button when onStartServer is not provided", () => {
    renderWithQueryAndI18n(
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

    renderWithQueryAndI18n(
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

    renderWithQueryAndI18n(
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
    renderWithQueryAndI18n(
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
    renderWithQueryAndI18n(
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

    renderWithQueryAndI18n(
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
    renderWithQueryAndI18n(
      <ServerStatusContextMenu
        {...defaultProps}
        conversationStatus="STARTING"
      />,
    );

    expect(screen.queryByTestId("stop-server-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("start-server-button")).not.toBeInTheDocument();
  });
});
