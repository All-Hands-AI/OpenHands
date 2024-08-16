import React from "react";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import ChatInput from "./ChatInput";

describe("ChatInput", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  const onSendMessage = vi.fn();

  it("should render a textarea", () => {
    render(<ChatInput onSendMessage={onSendMessage} />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("should be able to be set as disabled", async () => {
    const user = userEvent.setup();
    render(<ChatInput disabled onSendMessage={onSendMessage} />);

    const textarea = screen.getByRole("textbox");
    const button = screen.getByRole("button");

    expect(textarea).not.toBeDisabled(); // user can still type
    expect(button).toBeDisabled(); // user cannot submit

    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Enter}");

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should render with a placeholder", () => {
    render(<ChatInput onSendMessage={onSendMessage} />);

    const textarea = screen.getByPlaceholderText(
      /CHAT_INTERFACE\$INPUT_PLACEHOLDER/i,
    );
    expect(textarea).toBeInTheDocument();
  });

  it("should render a send button", () => {
    render(<ChatInput onSendMessage={onSendMessage} />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("should call sendChatMessage with the input when the send button is clicked", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSendMessage={onSendMessage} />);

    const textarea = screen.getByRole("textbox");
    const button = screen.getByRole("button");

    await user.type(textarea, "Hello, world!");
    await user.click(button);

    expect(onSendMessage).toHaveBeenCalledWith("Hello, world!", []);
    // Additionally, check if it was called exactly once
    expect(onSendMessage).toHaveBeenCalledTimes(1);
  });

  it("should be able to send a message when the enter key is pressed", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Enter}");

    expect(onSendMessage).toHaveBeenCalledWith("Hello, world!", []);
  });

  it("should NOT send a message when shift + enter is pressed", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Shift>} {Enter}"); // Shift + Enter

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should NOT send an empty message", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = screen.getByRole("textbox");
    const button = screen.getByRole("button");

    await user.type(textarea, " ");

    // with enter key
    await user.keyboard("{Enter}");
    expect(onSendMessage).not.toHaveBeenCalled();

    // with button click
    await user.click(button);
    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should clear the input message after sending a message", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = screen.getByRole("textbox");
    const button = screen.getByRole("button");

    await user.type(textarea, "Hello, world!");
    expect(textarea).toHaveValue("Hello, world!");

    await user.click(button);
    expect(textarea).toHaveValue("");
  });

  // this is already implemented but need to figure out how to test it
  it.todo(
    "should NOT send a message when the enter key is pressed while composing",
  );
});
