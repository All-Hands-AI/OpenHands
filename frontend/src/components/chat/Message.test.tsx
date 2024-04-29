import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import React from "react";
import ChatMessage from "./Message";

describe("Message", () => {
  it("should render a user message", () => {
    render(<ChatMessage message={{ sender: "user", content: "Hello" }} />);

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hello")).toHaveClass("self-end"); // user message should be on the right side
  });

  it("should render an assistant message", () => {
    render(<ChatMessage message={{ sender: "assistant", content: "Hi" }} />);

    expect(screen.getByText("Hi")).toBeInTheDocument();
    expect(screen.getByText("Hi")).not.toHaveClass("self-end"); // assistant message should be on the left side
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
