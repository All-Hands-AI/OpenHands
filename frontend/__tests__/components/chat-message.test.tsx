import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, test } from "vitest";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { FilesProvider } from "#/context/files";

describe("ChatMessage", () => {
  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <FilesProvider>
        {ui}
      </FilesProvider>
    );
  };
  it("should render a user message", () => {
    renderWithProvider(<ChatMessage type="user" message="Hello, World!" />);
    expect(screen.getByTestId("user-message")).toBeInTheDocument();
    expect(screen.getByText("Hello, World!")).toBeInTheDocument();
  });

  it("should render an assistant message", () => {
    renderWithProvider(<ChatMessage type="assistant" message="Hello, World!" />);
    expect(screen.getByTestId("assistant-message")).toBeInTheDocument();
    expect(screen.getByText("Hello, World!")).toBeInTheDocument();
  });

  it.skip("should support code syntax highlighting", () => {
    const code = "```js\nconsole.log('Hello, World!')\n```";
    renderWithProvider(<ChatMessage type="user" message={code} />);

    // SyntaxHighlighter breaks the code blocks into "tokens"
    expect(screen.getByText("console")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("'Hello, World!'")).toBeInTheDocument();
  });

  it.todo("should support markdown content");

  it("should render the copy to clipboard button when the user hovers over the message", async () => {
    const user = userEvent.setup();
    renderWithProvider(<ChatMessage type="user" message="Hello, World!" />);
    const message = screen.getByText("Hello, World!");

    expect(screen.getByTestId("copy-to-clipboard")).not.toBeVisible();

    await user.hover(message);

    expect(screen.getByTestId("copy-to-clipboard")).toBeVisible();
  });

  it("should copy content to clipboard", async () => {
    const user = userEvent.setup();
    renderWithProvider(<ChatMessage type="user" message="Hello, World!" />);
    const copyToClipboardButton = screen.getByTestId("copy-to-clipboard");

    await user.click(copyToClipboardButton);

    expect(navigator.clipboard.readText()).resolves.toBe("Hello, World!");
  });

  // BUG: vi.useFakeTimers() seems to break the tests
  it.todo(
    "should display a checkmark for 200ms and disable the button after copying content to clipboard",
  );

  it("should display an error toast if copying content to clipboard fails", async () => {});

  test.todo("push a toast after successfully copying content to clipboard");

  it("should render a component passed as a prop", () => {
    function Component() {
      return <div data-testid="custom-component">Custom Component</div>;
    }
    renderWithProvider(
      <ChatMessage type="user" message="Hello, World">
        <Component />
      </ChatMessage>,
    );
    expect(screen.getByTestId("custom-component")).toBeInTheDocument();
  });

  it("should apply correct styles to inline code", () => {
    renderWithProvider(<ChatMessage type="assistant" message="Here is some `inline code` text" />);
    const codeElement = screen.getByText("inline code");

    expect(codeElement.tagName.toLowerCase()).toBe("code");
    expect(codeElement.closest("article")).not.toBeNull();
  });
});
