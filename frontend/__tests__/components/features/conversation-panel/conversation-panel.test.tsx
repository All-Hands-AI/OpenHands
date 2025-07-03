import { screen, waitFor, within } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClientConfig } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import React from "react";
import { renderWithProviders } from "test-utils";
import { ConversationPanel } from "#/components/features/conversation-panel/conversation-panel";
import OpenHands from "#/api/open-hands";
import { Conversation } from "#/api/open-hands.types";

describe("ConversationPanel", () => {
  const onCloseMock = vi.fn();
  const RouterStub = createRoutesStub([
    {
      Component: () => <ConversationPanel onClose={onCloseMock} />,
      path: "/",
    },
  ]);

  const renderConversationPanel = (config?: QueryClientConfig) =>
    renderWithProviders(<RouterStub />, {
      preloadedState: {
        metrics: {
          cost: null,
          max_budget_per_task: null,
          usage: null,
        },
      },
    });

  beforeAll(() => {
    vi.mock("react-router", async (importOriginal) => ({
      ...(await importOriginal<typeof import("react-router")>()),
      Link: ({ children }: React.PropsWithChildren) => children,
      useNavigate: vi.fn(() => vi.fn()),
      useLocation: vi.fn(() => ({ pathname: "/conversation" })),
      useParams: vi.fn(() => ({ conversationId: "2" })),
    }));
  });

  const mockConversations: Conversation[] = [
    {
      conversation_id: "1",
      title: "Conversation 1",
      selected_repository: null,
      git_provider: null,
      selected_branch: null,
      last_updated_at: "2021-10-01T12:00:00Z",
      created_at: "2021-10-01T12:00:00Z",
      status: "STOPPED" as const,
      runtime_status: null,
      url: null,
      session_api_key: null,
    },
    {
      conversation_id: "2",
      title: "Conversation 2",
      selected_repository: null,
      git_provider: null,
      selected_branch: null,
      last_updated_at: "2021-10-02T12:00:00Z",
      created_at: "2021-10-02T12:00:00Z",
      status: "STOPPED" as const,
      runtime_status: null,
      url: null,
      session_api_key: null,
    },
    {
      conversation_id: "3",
      title: "Conversation 3",
      selected_repository: null,
      git_provider: null,
      selected_branch: null,
      last_updated_at: "2021-10-03T12:00:00Z",
      created_at: "2021-10-03T12:00:00Z",
      status: "STOPPED" as const,
      runtime_status: null,
      url: null,
      session_api_key: null,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
    // Setup default mock for getUserConversations
    vi.spyOn(OpenHands, "getUserConversations").mockResolvedValue([
      ...mockConversations,
    ]);
  });

  it("should render the conversations", async () => {
    renderConversationPanel();
    const cards = await screen.findAllByTestId("conversation-card");

    // NOTE that we filter out conversations that don't have a created_at property
    // (mock data has 4 conversations, but only 3 have a created_at property)
    expect(cards).toHaveLength(3);
  });

  it("should display an empty state when there are no conversations", async () => {
    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockResolvedValue([]);

    renderConversationPanel();

    const emptyState = await screen.findByText("CONVERSATION$NO_CONVERSATIONS");
    expect(emptyState).toBeInTheDocument();
  });

  it("should handle an error when fetching conversations", async () => {
    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockRejectedValue(
      new Error("Failed to fetch conversations"),
    );

    renderConversationPanel();

    const error = await screen.findByText("Failed to fetch conversations");
    expect(error).toBeInTheDocument();
  });

  it("should cancel deleting a conversation", async () => {
    const user = userEvent.setup();
    renderConversationPanel();

    let cards = await screen.findAllByTestId("conversation-card");
    expect(
      within(cards[0]).queryByTestId("delete-button"),
    ).not.toBeInTheDocument();

    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the first delete button
    await user.click(deleteButton);

    // Cancel the deletion
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    expect(
      screen.queryByRole("button", { name: /cancel/i }),
    ).not.toBeInTheDocument();

    // Ensure the conversation is not deleted
    cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(3);
  });

  it("should delete a conversation", async () => {
    const user = userEvent.setup();
    const mockData: Conversation[] = [
      {
        conversation_id: "1",
        title: "Conversation 1",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-01T12:00:00Z",
        created_at: "2021-10-01T12:00:00Z",
        status: "STOPPED" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "2",
        title: "Conversation 2",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-02T12:00:00Z",
        created_at: "2021-10-02T12:00:00Z",
        status: "STOPPED" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "3",
        title: "Conversation 3",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-03T12:00:00Z",
        created_at: "2021-10-03T12:00:00Z",
        status: "STOPPED" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
    ];

    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockImplementation(async () => mockData);

    const deleteUserConversationSpy = vi.spyOn(
      OpenHands,
      "deleteUserConversation",
    );
    deleteUserConversationSpy.mockImplementation(async (id: string) => {
      const index = mockData.findIndex((conv) => conv.conversation_id === id);
      if (index !== -1) {
        mockData.splice(index, 1);
      }
    });

    renderConversationPanel();

    const cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(3);

    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the first delete button
    await user.click(deleteButton);

    // Confirm the deletion
    const confirmButton = screen.getByRole("button", { name: /confirm/i });
    await user.click(confirmButton);

    expect(
      screen.queryByRole("button", { name: /confirm/i }),
    ).not.toBeInTheDocument();

    // Wait for the cards to update
    await waitFor(() => {
      const updatedCards = screen.getAllByTestId("conversation-card");
      expect(updatedCards).toHaveLength(2);
    });
  });

  it("should call onClose after clicking a card", async () => {
    const user = userEvent.setup();
    renderConversationPanel();
    const cards = await screen.findAllByTestId("conversation-card");
    const firstCard = cards[1];

    await user.click(firstCard);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });

  it("should refetch data on rerenders", async () => {
    const user = userEvent.setup();
    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockResolvedValue([...mockConversations]);

    function PanelWithToggle() {
      const [isOpen, setIsOpen] = React.useState(true);
      return (
        <>
          <button type="button" onClick={() => setIsOpen((prev) => !prev)}>
            Toggle
          </button>
          {isOpen && <ConversationPanel onClose={onCloseMock} />}
        </>
      );
    }

    const MyRouterStub = createRoutesStub([
      {
        Component: PanelWithToggle,
        path: "/",
      },
    ]);

    renderWithProviders(<MyRouterStub />, {
      preloadedState: {
        metrics: {
          cost: null,
          max_budget_per_task: null,
          usage: null,
        },
      },
    });

    const toggleButton = screen.getByText("Toggle");

    // Initial render
    const cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(3);

    // Toggle off
    await user.click(toggleButton);
    expect(screen.queryByTestId("conversation-card")).not.toBeInTheDocument();

    // Toggle on
    await user.click(toggleButton);
    const newCards = await screen.findAllByTestId("conversation-card");
    expect(newCards).toHaveLength(3);
  });

  it("should cancel stopping a conversation", async () => {
    const user = userEvent.setup();

    // Create mock data with a RUNNING conversation
    const mockRunningConversations: Conversation[] = [
      {
        conversation_id: "1",
        title: "Running Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-01T12:00:00Z",
        created_at: "2021-10-01T12:00:00Z",
        status: "RUNNING" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "2",
        title: "Starting Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-02T12:00:00Z",
        created_at: "2021-10-02T12:00:00Z",
        status: "STARTING" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "3",
        title: "Stopped Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-03T12:00:00Z",
        created_at: "2021-10-03T12:00:00Z",
        status: "STOPPED" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
    ];

    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockResolvedValue(mockRunningConversations);

    renderConversationPanel();

    const cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(3);

    // Click ellipsis on the first card (RUNNING status)
    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    // Stop button should be available for RUNNING conversation
    const stopButton = screen.getByTestId("stop-button");
    expect(stopButton).toBeInTheDocument();

    // Click the stop button
    await user.click(stopButton);

    // Cancel the stopping action
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    expect(
      screen.queryByRole("button", { name: /cancel/i }),
    ).not.toBeInTheDocument();

    // Ensure the conversation status hasn't changed
    const updatedCards = await screen.findAllByTestId("conversation-card");
    expect(updatedCards).toHaveLength(3);
  });

  it("should stop a conversation", async () => {
    const user = userEvent.setup();

    const mockData: Conversation[] = [
      {
        conversation_id: "1",
        title: "Running Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-01T12:00:00Z",
        created_at: "2021-10-01T12:00:00Z",
        status: "RUNNING" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "2",
        title: "Starting Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-02T12:00:00Z",
        created_at: "2021-10-02T12:00:00Z",
        status: "STARTING" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
    ];

    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockImplementation(async () => mockData);

    const stopConversationSpy = vi.spyOn(OpenHands, "stopConversation");
    stopConversationSpy.mockImplementation(async (id: string) => {
      const conversation = mockData.find((conv) => conv.conversation_id === id);
      if (conversation) {
        conversation.status = "STOPPED";
        return conversation;
      }
      return null;
    });

    renderConversationPanel();

    const cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(2);

    // Click ellipsis on the first card (RUNNING status)
    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const stopButton = screen.getByTestId("stop-button");

    // Click the stop button
    await user.click(stopButton);

    // Confirm the stopping action
    const confirmButton = screen.getByRole("button", { name: /confirm/i });
    await user.click(confirmButton);

    expect(
      screen.queryByRole("button", { name: /confirm/i }),
    ).not.toBeInTheDocument();

    // Verify the API was called
    expect(stopConversationSpy).toHaveBeenCalledWith("1");
    expect(stopConversationSpy).toHaveBeenCalledTimes(1);
  });

  it("should only show stop button for STARTING or RUNNING conversations", async () => {
    const user = userEvent.setup();

    const mockMixedStatusConversations: Conversation[] = [
      {
        conversation_id: "1",
        title: "Running Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-01T12:00:00Z",
        created_at: "2021-10-01T12:00:00Z",
        status: "RUNNING" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "2",
        title: "Starting Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-02T12:00:00Z",
        created_at: "2021-10-02T12:00:00Z",
        status: "STARTING" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
      {
        conversation_id: "3",
        title: "Stopped Conversation",
        selected_repository: null,
        git_provider: null,
        selected_branch: null,
        last_updated_at: "2021-10-03T12:00:00Z",
        created_at: "2021-10-03T12:00:00Z",
        status: "STOPPED" as const,
        runtime_status: null,
        url: null,
        session_api_key: null,
      },
    ];

    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockResolvedValue(mockMixedStatusConversations);

    renderConversationPanel();

    const cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(3);

    // Test RUNNING conversation - should show stop button
    const runningEllipsisButton = within(cards[0]).getByTestId(
      "ellipsis-button",
    );
    await user.click(runningEllipsisButton);

    expect(screen.getByTestId("stop-button")).toBeInTheDocument();

    // Click outside to close the menu
    await user.click(document.body);

    // Test STARTING conversation - should show stop button
    const startingEllipsisButton = within(cards[1]).getByTestId(
      "ellipsis-button",
    );
    await user.click(startingEllipsisButton);

    expect(screen.getByTestId("stop-button")).toBeInTheDocument();

    // Click outside to close the menu
    await user.click(document.body);

    // Test STOPPED conversation - should NOT show stop button
    const stoppedEllipsisButton = within(cards[2]).getByTestId(
      "ellipsis-button",
    );
    await user.click(stoppedEllipsisButton);

    expect(screen.queryByTestId("stop-button")).not.toBeInTheDocument();
  });
});
