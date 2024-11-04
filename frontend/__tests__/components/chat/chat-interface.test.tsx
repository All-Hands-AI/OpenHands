import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { ChatInterface } from "#/components/chat-interface";
import { addUserMessage } from "#/state/chatSlice";
import { SUGGESTIONS } from "#/utils/suggestions";
import * as ChatSlice from "#/state/chatSlice";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const renderChatInterface = (messages: (Message | ErrorMessage)[]) =>
  renderWithProviders(<ChatInterface />);

describe("ChatInterface", () => {
  beforeAll(() => {
    // mock useScrollToBottom hook
    vi.mock("#/hooks/useScrollToBottom", () => ({
      useScrollToBottom: vi.fn(() => ({
        scrollDomToBottom: vi.fn(),
        onChatBodyScroll: vi.fn(),
        hitBottom: vi.fn(),
      })),
    }));
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe.only("Empty state", () => {
    it("should render suggestions if empty", () => {
      const { store } = renderWithProviders(<ChatInterface />, {
        preloadedState: {
          chat: { messages: [] },
        },
      });

      expect(screen.getByTestId("suggestions")).toBeInTheDocument();

      act(() => {
        store.dispatch(
          addUserMessage({
            content: "Hello",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }),
        );
      });

      expect(screen.queryByTestId("suggestions")).not.toBeInTheDocument();
    });

    it("should render the default suggestions", () => {
      renderWithProviders(<ChatInterface />, {
        preloadedState: {
          chat: { messages: [] },
        },
      });

      const suggestions = screen.getByTestId("suggestions");
      const defaultSuggestions = Object.keys(SUGGESTIONS["non-repo"]);

      // check that there are at most 4 suggestions displayed
      const displayedSuggestions = within(suggestions).getAllByRole("button");
      expect(displayedSuggestions.length).toBeLessThanOrEqual(4);

      // Check that each displayed suggestion is one of the default suggestions
      displayedSuggestions.forEach((suggestion) => {
        expect(defaultSuggestions).toContain(suggestion.textContent);
      });
    });

    it.todo(
      "should render the other suggestions if the user selected to cloned a repo",
    );

    it("should dispatch a user message when selecting a message", async () => {
      const addUserMessageSpy = vi.spyOn(ChatSlice, "addUserMessage");
      const user = userEvent.setup();
      const { store } = renderWithProviders(<ChatInterface />, {
        preloadedState: {
          chat: { messages: [] },
        },
      });

      const suggestions = screen.getByTestId("suggestions");
      const displayedSuggestions = within(suggestions).getAllByRole("button");

      await user.click(displayedSuggestions[0]);

      // user message has been dispatched
      expect(addUserMessageSpy).toHaveBeenCalled();
      expect(screen.queryByTestId("suggestions")).not.toBeInTheDocument();
      expect(store.getState().chat.messages).toHaveLength(1);
    });
  });

  it("should render messages", () => {
    const messages: Message[] = [
      {
        sender: "user",
        content: "Hello",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
      {
        sender: "assistant",
        content: "Hi",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    ];
    renderChatInterface(messages);

    expect(screen.getAllByTestId(/-message/)).toHaveLength(2);
  });

  it("should render a chat input", () => {
    const messages: Message[] = [];
    renderChatInterface(messages);

    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
  });

  it.todo("should call socket send when submitting a message", async () => {
    const user = userEvent.setup();
    const messages: Message[] = [];
    renderChatInterface(messages);

    const input = screen.getByTestId("chat-input");
    await user.type(input, "Hello");
    await user.keyboard("{Enter}");

    // spy on send and expect to have been called
  });

  it("should render an image carousel with a message", () => {
    let messages: Message[] = [
      {
        sender: "assistant",
        content: "Here are some images",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    ];
    const { rerender } = renderChatInterface(messages);

    expect(screen.queryByTestId("image-carousel")).not.toBeInTheDocument();

    messages = [
      {
        sender: "assistant",
        content: "Here are some images",
        imageUrls: ["image1", "image2"],
        timestamp: new Date().toISOString(),
      },
    ];

    rerender(<ChatInterface />);

    const imageCarousel = screen.getByTestId("image-carousel");
    expect(imageCarousel).toBeInTheDocument();
    expect(within(imageCarousel).getAllByTestId("image-preview")).toHaveLength(
      2,
    );
  });

  it.todo("should render confirmation buttons");

  it("should render a 'continue' action when there are more than 2 messages and awaiting user input", () => {
    const messages: Message[] = [
      {
        sender: "assistant",
        content: "Hello",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
      {
        sender: "user",
        content: "Hi",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    ];
    const { rerender } = renderChatInterface(messages);
    expect(
      screen.queryByTestId("continue-action-button"),
    ).not.toBeInTheDocument();

    messages.push({
      sender: "assistant",
      content: "How can I help you?",
      imageUrls: [],
      timestamp: new Date().toISOString(),
    });

    rerender(<ChatInterface />);

    expect(screen.getByTestId("continue-action-button")).toBeInTheDocument();
  });

  it("should render inline errors", () => {
    const messages: (Message | ErrorMessage)[] = [
      {
        sender: "assistant",
        content: "Hello",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
      {
        error: "Woops!",
        message: "Something went wrong",
      },
    ];
    renderChatInterface(messages);

    const error = screen.getByTestId("error-message");
    expect(within(error).getByText("Woops!")).toBeInTheDocument();
    expect(within(error).getByText("Something went wrong")).toBeInTheDocument();
  });

  it("should render feedback actions if there are more than 3 messages", () => {
    const messages: Message[] = [
      {
        sender: "assistant",
        content: "Hello",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
      {
        sender: "user",
        content: "Hi",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
      {
        sender: "assistant",
        content: "How can I help you?",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    ];
    const { rerender } = renderChatInterface(messages);
    expect(screen.queryByTestId("feedback-actions")).not.toBeInTheDocument();

    messages.push({
      sender: "user",
      content: "I need help",
      imageUrls: [],
      timestamp: new Date().toISOString(),
    });

    rerender(<ChatInterface />);

    expect(screen.getByTestId("feedback-actions")).toBeInTheDocument();
  });

  describe("feedback", () => {
    it.todo("should open the feedback modal when a feedback action is clicked");
    it.todo(
      "should submit feedback and hide the actions when feedback is shared",
    );
    it.todo("should render the actions once more after new messages are added");
  });
});
