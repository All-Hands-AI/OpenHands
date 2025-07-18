import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderWithProviders } from "test-utils";
import { MicroagentsModal } from "#/components/features/conversation-panel/microagents-modal";
import OpenHands from "#/api/open-hands";
import { AgentState } from "#/types/agent-state";

vi.mock("react-redux", async () => {
  const actual = await vi.importActual("react-redux");
  return {
    ...actual,
    useDispatch: () => vi.fn(),
    useSelector: () => ({
      agent: {
        curAgentState: AgentState.AWAITING_USER_INPUT,
      },
    }),
  };
});

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

    // Setup default mock for getUserConversations
    vi.spyOn(OpenHands, "getMicroagents").mockResolvedValue({
      microagents: mockMicroagents,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("Refresh Button Rendering", () => {
    it("should render the refresh button with correct text and test ID", () => {
      renderWithProviders(<MicroagentsModal {...defaultProps} />);

      const refreshButton = screen.getByTestId("refresh-microagents");
      expect(refreshButton).toBeInTheDocument();
      expect(refreshButton).toHaveTextContent("BUTTON$REFRESH");
    });
  });

  describe("Refresh Button Functionality", () => {
    it("should call refetch when refresh button is clicked", async () => {
      const user = userEvent.setup();

      renderWithProviders(<MicroagentsModal {...defaultProps} />);

      const refreshSpy = vi.spyOn(OpenHands, "getMicroagents");

      const refreshButton = screen.getByTestId("refresh-microagents");
      await user.click(refreshButton);

      expect(refreshSpy).toHaveBeenCalledTimes(1);
    });
  });
});
