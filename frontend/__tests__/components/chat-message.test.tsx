import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { ChatMessage } from "#/components/features/chat/chat-message";

describe("ChatMessage", () => {
  it("should render a user message", () => {
    render(<ChatMessage type="user" message="Hello, World!" />);
    expect(screen.getByTestId("user-message")).toBeInTheDocument();
    expect(screen.getByText("Hello, World!")).toBeInTheDocument();
  });

  it("should support code syntax highlighting", () => {
    const code = "```js\nconsole.log('Hello, World!')\n```";
    render(<ChatMessage type="user" message={code} />);

    // SyntaxHighlighter breaks the code blocks into "tokens"
    expect(screen.getByText("console")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("'Hello, World!'")).toBeInTheDocument();
  });

  it("should render the copy to clipboard button when the user hovers over the message", async () => {
    const user = userEvent.setup();
    render(<ChatMessage type="user" message="Hello, World!" />);
    const message = screen.getByText("Hello, World!");

    expect(screen.getByTestId("copy-to-clipboard")).not.toBeVisible();

    await user.hover(message);

    expect(screen.getByTestId("copy-to-clipboard")).toBeVisible();
  });

  it("should copy content to clipboard", async () => {
    const user = userEvent.setup();
    render(<ChatMessage type="user" message="Hello, World!" />);
    const copyToClipboardButton = screen.getByTestId("copy-to-clipboard");

    await user.click(copyToClipboardButton);

    await waitFor(() =>
      expect(navigator.clipboard.readText()).resolves.toBe("Hello, World!"),
    );
  });

  it("should render a component passed as a prop", () => {
    function Component() {
      return <div data-testid="custom-component">Custom Component</div>;
    }
    render(
      <ChatMessage type="user" message="Hello, World">
        <Component />
      </ChatMessage>,
    );
    expect(screen.getByTestId("custom-component")).toBeInTheDocument();
  });

  it("should apply correct styles to inline code", () => {
    render(
      <ChatMessage type="agent" message="Here is some `inline code` text" />,
    );
    const codeElement = screen.getByText("inline code");

    expect(codeElement.tagName.toLowerCase()).toBe("code");
    expect(codeElement.closest("article")).not.toBeNull();
  });

  it("should render an action button on hover if provided", async () => {
    const user = userEvent.setup();
    const actionButton = (
      <button data-testid="action-button" type="button">
        Action
      </button>
    );
    render(
      <ChatMessage
        type="user"
        message="Hello, World!"
        actionButton={actionButton}
      />,
    );

    const message = screen.getByText("Hello, World!");

    expect(screen.queryByTestId("action-button")).not.toBeInTheDocument();

    await user.hover(message);
    expect(screen.getByTestId("action-button")).toBeVisible();

    await user.unhover(message);
    expect(screen.queryByTestId("action-button")).not.toBeInTheDocument();
  });
});
