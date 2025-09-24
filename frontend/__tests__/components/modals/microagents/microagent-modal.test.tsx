import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderWithQueryAndI18n } from "test-utils";
import { MicroagentsModal } from "#/components/features/conversation-panel/microagents-modal";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { AgentState } from "#/types/agent-state";
import { useAgentStore } from "#/stores/agent-store";

// Mock the agent store
vi.mock("#/stores/agent-store", () => ({
  useAgentStore: vi.fn(),
}));

// Mock the conversation ID hook
vi.mock("#/hooks/use-conversation-id", () => ({
  useConversationId: () => ({ conversationId: "test-conversation-id" }),
}));

describe("MicroagentsModal - Refresh Button", () => {
  const mockOnClose = vi.fn();
  const conversationId = "test-conversation-id";

  const defaultProps = {
    onClose: mockOnClose,
    conversationId,
  };

  const mockMicroagents = [
    {
      name: "Test Agent 1",
      type: "repo" as const,
      triggers: ["test", "example"],
      content: "This is test content for agent 1",
    },
    {
      name: "Test Agent 2",
      type: "knowledge" as const,
      triggers: ["help", "support"],
      content: "This is test content for agent 2",
    },
  ];

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();

    // Setup default mock for getMicroagents
    vi.spyOn(ConversationService, "getMicroagents").mockResolvedValue({
      microagents: mockMicroagents,
    });

    // Mock the agent store to return a ready state
    vi.mocked(useAgentStore).mockReturnValue({
      curAgentState: AgentState.AWAITING_USER_INPUT,
      setCurrentAgentState: vi.fn(),
      reset: vi.fn(),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("Refresh Button Rendering", () => {
    it("should render the refresh button with correct text and test ID", async () => {
      renderWithQueryAndI18n(<MicroagentsModal {...defaultProps} />);

      // Wait for the component to load and render the refresh button
      const refreshButton = await screen.findByTestId("refresh-microagents");
      expect(refreshButton).toBeInTheDocument();
      expect(refreshButton).toHaveTextContent("BUTTON$REFRESH");
    });
  });

  describe("Refresh Button Functionality", () => {
    it("should call refetch when refresh button is clicked", async () => {
      const user = userEvent.setup();

      renderWithQueryAndI18n(<MicroagentsModal {...defaultProps} />);

      const refreshSpy = vi.spyOn(ConversationService, "getMicroagents");

      // Wait for the component to load and render the refresh button
      const refreshButton = await screen.findByTestId("refresh-microagents");
      await user.click(refreshButton);

      expect(refreshSpy).toHaveBeenCalledTimes(1);
    });
  });
});
