import { render, screen } from "@testing-library/react";
import { describe, afterEach, vi, it, expect } from "vitest";
import { InteractiveChatBox } from "#/components/features/chat/interactive-chat-box";

describe("InteractiveChatBox", () => {
  const onSubmitMock = vi.fn();
  const onStopMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the chat input", () => {
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />);
    expect(screen.getByTestId("interactive-chat-box")).toBeInTheDocument();
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
  });

  it("should not apply min-width when there is no text", () => {
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} value="" />);

    const chatInput = screen.getByTestId("chat-input").querySelector("textarea");
    expect(chatInput).toBeTruthy();
    expect(chatInput?.className).not.toContain("min-w-[300px]");
  });

  it("should apply min-width when there is text", () => {
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} value="Hello, world!" />);

    const chatInput = screen.getByTestId("chat-input").querySelector("textarea");
    expect(chatInput).toBeTruthy();
    expect(chatInput?.className).toContain("min-w-[300px]");
  });
});