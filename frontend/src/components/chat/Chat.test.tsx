import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "test-utils";
import Chat from "./Chat";

const MESSAGES: Message[] = [
  { sender: "assistant", content: "Hello!" },
  { sender: "user", content: "Hi!" },
  { sender: "assistant", content: "How can I help you today?" },
];

describe("Chat", () => {
  it("should render chat messages", () => {
    renderWithProviders(<Chat messages={MESSAGES} />);

    const messages = screen.getAllByTestId("message");
    expect(messages).toHaveLength(MESSAGES.length);
  });
});
