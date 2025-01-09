import { render, screen, within } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import {
  QueryClientProvider,
  QueryClient,
  QueryClientConfig,
} from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { ConversationPanel } from "#/components/features/conversation-panel/conversation-panel";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import { clickOnEditButton } from "./utils";

describe("ConversationPanel", () => {
  const onCloseMock = vi.fn();
  const RouterStub = createRoutesStub([
    {
      Component: () => <ConversationPanel onClose={onCloseMock} />,
      path: "/",
    },
  ]);

  const renderConversationPanel = (config?: QueryClientConfig) =>
    render(<RouterStub />, {
      wrapper: ({ children }) => (
        <AuthProvider>
          <QueryClientProvider client={new QueryClient(config)}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      ),
    });

  const { endSessionMock } = vi.hoisted(() => ({
    endSessionMock: vi.fn(),
  }));

  beforeAll(() => {
    vi.mock("react-router", async (importOriginal) => ({
      ...(await importOriginal<typeof import("react-router")>()),
      Link: ({ children }: React.PropsWithChildren) => children,
      useNavigate: vi.fn(() => vi.fn()),
      useLocation: vi.fn(() => ({ pathname: "/conversation" })),
      useParams: vi.fn(() => ({ conversationId: "2" })),
    }));

    vi.mock("#/hooks/use-end-session", async (importOriginal) => ({
      ...(await importOriginal<typeof import("#/hooks/use-end-session")>()),
      useEndSession: vi.fn(() => endSessionMock),
    }));
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
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

    const emptyState = await screen.findByText("No conversations found");
    expect(emptyState).toBeInTheDocument();
  });

  it("should handle an error when fetching conversations", async () => {
    const getUserConversationsSpy = vi.spyOn(OpenHands, "getUserConversations");
    getUserConversationsSpy.mockRejectedValue(
      new Error("Failed to fetch conversations"),
    );

    renderConversationPanel({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

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
    const cancelButton = screen.getByText("Cancel");
    await user.click(cancelButton);

    expect(screen.queryByText("Cancel")).not.toBeInTheDocument();

    // Ensure the conversation is not deleted
    cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(3);
  });

  it("should call endSession after deleting a conversation that is the current session", async () => {
    const user = userEvent.setup();
    renderConversationPanel();

    let cards = await screen.findAllByTestId("conversation-card");
    const ellipsisButton = within(cards[1]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the second delete button
    await user.click(deleteButton);

    // Confirm the deletion
    const confirmButton = screen.getByText("Confirm");
    await user.click(confirmButton);

    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();

    // Ensure the conversation is deleted
    cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(2);

    expect(endSessionMock).toHaveBeenCalledOnce();
  });

  it("should delete a conversation", async () => {
    const user = userEvent.setup();
    renderConversationPanel();

    let cards = await screen.findAllByTestId("conversation-card");
    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the first delete button
    await user.click(deleteButton);

    // Confirm the deletion
    const confirmButton = screen.getByText("Confirm");
    await user.click(confirmButton);

    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();

    // Ensure the conversation is deleted
    cards = await screen.findAllByTestId("conversation-card");
    expect(cards).toHaveLength(1);
  });

  it("should rename a conversation", async () => {
    const updateUserConversationSpy = vi.spyOn(
      OpenHands,
      "updateUserConversation",
    );

    const user = userEvent.setup();
    renderConversationPanel();
    const cards = await screen.findAllByTestId("conversation-card");
    const title = within(cards[0]).getByTestId("conversation-card-title");

    await clickOnEditButton(user);

    await user.clear(title);
    await user.type(title, "Conversation 1 Renamed");
    await user.tab();

    // Ensure the conversation is renamed
    expect(updateUserConversationSpy).toHaveBeenCalledWith("3", {
      title: "Conversation 1 Renamed",
    });
  });

  it("should not rename a conversation when the name is unchanged", async () => {
    const updateUserConversationSpy = vi.spyOn(
      OpenHands,
      "updateUserConversation",
    );

    const user = userEvent.setup();
    renderConversationPanel();
    const cards = await screen.findAllByTestId("conversation-card");
    const title = within(cards[0]).getByTestId("conversation-card-title");

    await user.click(title);
    await user.tab();

    // Ensure the conversation is not renamed
    expect(updateUserConversationSpy).not.toHaveBeenCalled();

    await clickOnEditButton(user);

    await user.type(title, "Conversation 1");
    await user.click(title);
    await user.tab();

    expect(updateUserConversationSpy).toHaveBeenCalledTimes(1);

    await user.click(title);
    await user.tab();

    expect(updateUserConversationSpy).toHaveBeenCalledTimes(1);
  });

  it("should call onClose after clicking a card", async () => {
    renderConversationPanel();
    const cards = await screen.findAllByTestId("conversation-card");
    const firstCard = cards[0];

    await userEvent.click(firstCard);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});
