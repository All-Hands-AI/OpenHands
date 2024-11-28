import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { addUserMessage } from "#/state/chat-slice";
import { SUGGESTIONS } from "#/utils/suggestions";
import * as ChatSlice from "#/state/chat-slice";
import { WsClientProviderStatus } from "#/context/ws-client-provider";
import { ChatInterface } from "#/routes/_oh.app/chat-interface";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const renderChatInterface = (messages: (Message | ErrorMessage)[]) =>
  renderWithProviders(<ChatInterface />);

describe("Empty state", () => {
  const { send: sendMock } = vi.hoisted(() => ({
    send: vi.fn(),
  }));

  const { useWsClient: useWsClientMock } = vi.hoisted(() => ({
    useWsClient: vi.fn(() => ({
      send: sendMock,
      status: WsClientProviderStatus.ACTIVE,
      isLoadingMessages: false,
    })),
  }));

  beforeAll(() => {
    vi.mock("@remix-run/react", async (importActual) => ({
      ...(await importActual<typeof import("@remix-run/react")>()),
      useRouteLoaderData: vi.fn(() => ({})),
    }));

    vi.mock("#/context/socket", async (importActual) => ({
      ...(await importActual<typeof import("#/context/ws-client-provider")>()),
      useWsClient: useWsClientMock,
    }));
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

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
    const repoSuggestions = Object.keys(SUGGESTIONS.repo);

    // check that there are at most 4 suggestions displayed
    const displayedSuggestions = within(suggestions).getAllByRole("button");
    expect(displayedSuggestions.length).toBeLessThanOrEqual(4);

    // Check that each displayed suggestion is one of the repo suggestions
    displayedSuggestions.forEach((suggestion) => {
      expect(repoSuggestions).toContain(suggestion.textContent);
    });
  });

  it.fails(
    "should load the a user message to the input when selecting",
    async () => {
      // this is to test that the message is in the UI before the socket is called
      useWsClientMock.mockImplementation(() => ({
        send: sendMock,
        status: WsClientProviderStatus.ACTIVE,
        isLoadingMessages: false,
      }));
      const addUserMessageSpy = vi.spyOn(ChatSlice, "addUserMessage");
      const user = userEvent.setup();
      const { store } = renderWithProviders(<ChatInterface />, {
        preloadedState: {
          chat: { messages: [] },
        },
      });

      const suggestions = screen.getByTestId("suggestions");
      const displayedSuggestions = within(suggestions).getAllByRole("button");
      const input = screen.getByTestId("chat-input");

      await user.click(displayedSuggestions[0]);

      // user message loaded to input
      expect(addUserMessageSpy).not.toHaveBeenCalled();
      expect(screen.queryByTestId("suggestions")).toBeInTheDocument();
      expect(store.getState().chat.messages).toHaveLength(0);
      expect(input).toHaveValue(displayedSuggestions[0].textContent);
    },
  );

  it.fails(
    "should send the message to the socket only if the runtime is active",
    async () => {
      useWsClientMock.mockImplementation(() => ({
        send: sendMock,
        status: WsClientProviderStatus.ACTIVE,
        isLoadingMessages: false,
      }));
      const user = userEvent.setup();
      const { rerender } = renderWithProviders(<ChatInterface />, {
        preloadedState: {
          chat: { messages: [] },
        },
      });

      const suggestions = screen.getByTestId("suggestions");
      const displayedSuggestions = within(suggestions).getAllByRole("button");

      await user.click(displayedSuggestions[0]);
      expect(sendMock).not.toHaveBeenCalled();

      useWsClientMock.mockImplementation(() => ({
        send: sendMock,
        status: WsClientProviderStatus.ACTIVE,
        isLoadingMessages: false,
      }));
      rerender(<ChatInterface />);

      await waitFor(() =>
        expect(sendMock).toHaveBeenCalledWith(expect.any(String)),
      );
    },
  );
});

describe.skip("ChatInterface", () => {
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
        error: true,
        id: "",
        message: "Something went wrong",
      },
    ];
    renderChatInterface(messages);

    const error = screen.getByTestId("error-message");
    expect(within(error).getByText("Something went wrong")).toBeInTheDocument();
  });

  it("should render both GitHub buttons initially when ghToken is available", () => {
    vi.mock("@remix-run/react", async (importActual) => ({
      ...(await importActual<typeof import("@remix-run/react")>()),
      useRouteLoaderData: vi.fn(() => ({ ghToken: "test-token" })),
    }));

    const messages: Message[] = [
      {
        sender: "assistant",
        content: "Hello",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    ];
    renderChatInterface(messages);

    const pushButton = screen.getByRole("button", { name: "Push to Branch" });
    const prButton = screen.getByRole("button", { name: "Push & Create PR" });

    expect(pushButton).toBeInTheDocument();
    expect(prButton).toBeInTheDocument();
    expect(pushButton).toHaveTextContent("Push to Branch");
    expect(prButton).toHaveTextContent("Push & Create PR");
  });

  it("should render only 'Push changes to PR' button after PR is created", async () => {
    vi.mock("@remix-run/react", async (importActual) => ({
      ...(await importActual<typeof import("@remix-run/react")>()),
      useRouteLoaderData: vi.fn(() => ({ ghToken: "test-token" })),
    }));

    const messages: Message[] = [
      {
        sender: "assistant",
        content: "Hello",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    ];
    const { rerender } = renderChatInterface(messages);
    const user = userEvent.setup();

    // Click the "Push & Create PR" button
    const prButton = screen.getByRole("button", { name: "Push & Create PR" });
    await user.click(prButton);

    // Re-render to trigger state update
    rerender(<ChatInterface />);

    // Verify only one button is shown
    const pushToPrButton = screen.getByRole("button", {
      name: "Push changes to PR",
    });
    expect(pushToPrButton).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Push to Branch" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Push & Create PR" }),
    ).not.toBeInTheDocument();
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
