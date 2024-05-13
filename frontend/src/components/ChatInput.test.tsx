import React from "react";
import userEvent from "@testing-library/user-event";
import { act, render } from "@testing-library/react";
import ChatInput from "./ChatInput";

describe("ChatInput", () => {
  const onSendMessage = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render a textarea", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = getByRole("textbox");
    expect(textarea).toBeInTheDocument();
  });

  it("should be able to be set as disabled", () => {
    const { getByRole } = render(
      <ChatInput disabled onSendMessage={onSendMessage} />,
    );
    const textarea = getByRole("textbox");
    const button = getByRole("button");

    expect(textarea).not.toBeDisabled(); // user can still type
    expect(button).toBeDisabled(); // user cannot submit

    act(() => {
      userEvent.type(textarea, "Hello, world!{enter}");
    });

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should render with a placeholder", () => {
    const { getByPlaceholderText } = render(
      <ChatInput onSendMessage={onSendMessage} />,
    );
    const textarea = getByPlaceholderText(/CHAT_INTERFACE\$INPUT_PLACEHOLDER/i);
    expect(textarea).toBeInTheDocument();
  });

  it("should render a send button", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const button = getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("should call sendChatMessage with the input when the send button is clicked", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = getByRole("textbox");
    const button = getByRole("button");

    act(() => {
      userEvent.type(textarea, "Hello, world!");
      userEvent.click(button);
    });

    expect(onSendMessage).toHaveBeenCalledWith("Hello, world!");
  });

  it("should be able to send a message when the enter key is pressed", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = getByRole("textbox");

    act(() => {
      userEvent.type(textarea, "Hello, world!{enter}");
    });

    expect(onSendMessage).toHaveBeenCalledWith("Hello, world!");
  });

  it("should NOT send a message when shift + enter is pressed", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = getByRole("textbox");

    act(() => {
      userEvent.type(textarea, "Hello, world!{shift}{enter}");
    });

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should NOT send an empty message", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = getByRole("textbox");
    const button = getByRole("button");

    act(() => {
      userEvent.type(textarea, " {enter}"); // Only whitespace
    });

    expect(onSendMessage).not.toHaveBeenCalled();

    act(() => {
      userEvent.click(button);
    });

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should clear the input message after sending a message", () => {
    const { getByRole } = render(<ChatInput onSendMessage={onSendMessage} />);
    const textarea = getByRole("textbox");
    const button = getByRole("button");

    act(() => {
      userEvent.type(textarea, "Hello, world!");
    });

    expect(textarea).toHaveValue("Hello, world!");

    act(() => {
      userEvent.click(button);
    });

    expect(textarea).toHaveValue("");

    act(() => {
      userEvent.type(textarea, "Hello, world!{enter}");
    });

    expect(textarea).toHaveValue(""); // no new line
  });

  // this is already implemented but need to figure out how to test it
  it.todo(
    "should NOT send a message when the enter key is pressed while composing",
  );
});
