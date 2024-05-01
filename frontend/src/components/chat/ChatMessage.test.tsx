import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import React from "react";
import ChatMessage from "./ChatMessage";

describe("Message", () => {
  it("should render a user message", () => {
    render(<ChatMessage message={{ sender: "user", content: "Hello" }} />);

    expect(screen.getByTestId("chat-bubble")).toBeInTheDocument();
    expect(screen.getByTestId("chat-bubble")).toHaveClass("self-end"); // user message should be on the right side
  });

  it("should render an assistant message", () => {
    render(<ChatMessage message={{ sender: "assistant", content: "Hi" }} />);

    expect(screen.getByTestId("chat-bubble")).toBeInTheDocument();
    expect(screen.getByTestId("chat-bubble")).not.toHaveClass("self-end"); // assistant message should be on the left side
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

    expect(screen.getByText("console.log('Hello')")).toBeInTheDocument();
    expect(screen.getByText("console.log('Hello')")).toHaveClass("language-js");
  });
});
