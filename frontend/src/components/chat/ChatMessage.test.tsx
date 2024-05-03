import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import React from "react";
import ChatMessage from "./ChatMessage";

// avoid typing side-effect
vi.mock("#/hooks/useTyping", () => ({
  useTyping: vi.fn((text: string) => text),
}));

describe("Message", () => {
  it("should render a user message", () => {
    render(<ChatMessage message={{ sender: "user", content: "Hello" }} />);

    expect(screen.getByTestId("message")).toBeInTheDocument();
    expect(screen.getByTestId("message")).toHaveClass("self-end"); // user message should be on the right side
  });

  it("should render an assistant message", () => {
    render(<ChatMessage message={{ sender: "assistant", content: "Hi" }} />);

    expect(screen.getByTestId("message")).toBeInTheDocument();
    expect(screen.getByTestId("message")).not.toHaveClass("self-end"); // assistant message should be on the left side
  });

  it("should render markdown content", () => {
    render(
      <ChatMessage
        message={{
          sender: "user",
          content: "```js\nconsole.log('Hello')\n```",
        }}
      />,
    );

    // SyntaxHighlighter breaks the code blocks into "tokens"
    expect(screen.getByText("console")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("'Hello'")).toBeInTheDocument();
  });
});
