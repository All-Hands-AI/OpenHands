import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Chat from "./Chat";

const MESSAGES: Message[] = [
  { sender: "assistant", content: "Hello!" },
  { sender: "user", content: "Hi!" },
  { sender: "assistant", content: "How can I help you today?" },
];

HTMLElement.prototype.scrollTo = vi.fn(() => {});

describe("Chat", () => {
  it("should render chat messages", () => {
    render(<Chat messages={MESSAGES} />);

    const messages = screen.getAllByTestId("message");

    expect(messages).toHaveLength(MESSAGES.length);
  });
});
