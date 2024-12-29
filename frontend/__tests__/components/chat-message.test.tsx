import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, test, beforeEach } from "vitest";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { Provider } from "react-redux";
import configureStore from "redux-mock-store";

const mockStore = configureStore([]);

describe("ChatMessage", () => {
  let store;

  beforeEach(() => {
    store = mockStore({
      speech: {
        enabled: false,
      },
    });
  });

  const renderWithRedux = (component) => {
    return render(
      <Provider store={store}>
        {component}
      </Provider>
    );
  };

  it("should render a user message", () => {
    renderWithRedux(<ChatMessage type="user" message="Hello, World!" />);
    expect(screen.getByTestId("user-message")).toBeInTheDocument();
    expect(screen.getByText("Hello, World!")).toBeInTheDocument();
  });

  it("should render an assistant message", () => {
    renderWithRedux(<ChatMessage type="assistant" message="Hello, World!" />);
    expect(screen.getByTestId("assistant-message")).toBeInTheDocument();
    expect(screen.getByText("Hello, World!")).toBeInTheDocument();
  });

  it.skip("should support code syntax highlighting", () => {
    const code = "```js\nconsole.log('Hello, World!')\n```";
    renderWithRedux(<ChatMessage type="user" message={code} />);

    // SyntaxHighlighter breaks the code blocks into "tokens"
    expect(screen.getByText("console")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("'Hello, World!'")).toBeInTheDocument();
  });

  it("should render the copy to clipboard button when the user hovers over the message", async () => {
    const user = userEvent.setup();
    renderWithRedux(<ChatMessage type="user" message="Hello, World!" />);
    const message = screen.getByText("Hello, World!");

    expect(screen.getByTestId("copy-to-clipboard")).not.toBeVisible();

    await user.hover(message);

    expect(screen.getByTestId("copy-to-clipboard")).toBeVisible();
  });

  it("should copy content to clipboard", async () => {
    const user = userEvent.setup();
    renderWithRedux(<ChatMessage type="user" message="Hello, World!" />);
    const copyToClipboardButton = screen.getByTestId("copy-to-clipboard");

    await user.click(copyToClipboardButton);

    expect(navigator.clipboard.readText()).resolves.toBe("Hello, World!");
  });

  it("should display an error toast if copying content to clipboard fails", async () => {});

  it("should render a component passed as a prop", () => {
    function Component() {
      return <div data-testid="custom-component">Custom Component</div>;
    }
    renderWithRedux(
      <ChatMessage type="user" message="Hello, World">
        <Component />
      </ChatMessage>,
    );
    expect(screen.getByTestId("custom-component")).toBeInTheDocument();
  });

  it("should apply correct styles to inline code", () => {
    renderWithRedux(
      <ChatMessage
        type="assistant"
        message="Here is some `inline code` text"
      />,
    );
    const codeElement = screen.getByText("inline code");

    expect(codeElement.tagName.toLowerCase()).toBe("code");
    expect(codeElement.closest("article")).not.toBeNull();
  });
});
