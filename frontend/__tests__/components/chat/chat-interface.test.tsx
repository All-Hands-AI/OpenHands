import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInterface } from "#/components/chat-interface";
import { SocketProvider } from "#/context/socket";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const renderChatInterface = (messages: (Message | ErrorMessage)[]) =>
  render(<ChatInterface />, { wrapper: SocketProvider });

describe.skip("ChatInterface", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it.todo("should render suggestions if empty");

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
