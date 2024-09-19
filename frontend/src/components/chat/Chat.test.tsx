import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "test-utils";
import Chat from "./Chat";

const MESSAGES: Message[] = [
  {
    sender: "assistant",
    content: "Hello!",
    imageUrls: [],
    timestamp: new Date().toISOString(),
  },
  {
    sender: "user",
    content: "Hi!",
    imageUrls: [],
    timestamp: new Date().toISOString(),
  },
];

describe("Chat", () => {
  it("should render chat messages", () => {
    renderWithProviders(<Chat messages={MESSAGES} />);

    const messages = screen.getAllByTestId("article");
    expect(messages).toHaveLength(MESSAGES.length);
  });
});
