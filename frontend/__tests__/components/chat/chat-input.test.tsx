import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { describe, afterEach, vi, it, expect } from "vitest";
import { ChatInput } from "#/components/chat-input";

describe("ChatInput", () => {
  const onSubmitMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render a textarea", () => {
    render(<ChatInput onSubmit={onSubmitMock} />);
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("should call onSubmit when the user types and presses enter", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Enter}");

    expect(onSubmitMock).toHaveBeenCalledWith("Hello, world!");
  });

  it("should call onSubmit when pressing the submit button", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");
    const button = screen.getByRole("button");

    await user.type(textarea, "Hello, world!");
    await user.click(button);

    expect(onSubmitMock).toHaveBeenCalledWith("Hello, world!");
  });

  it("should not call onSubmit when the message is empty", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const button = screen.getByRole("button");

    await user.click(button);
    expect(onSubmitMock).not.toHaveBeenCalled();

    await user.keyboard("{Enter}");
    expect(onSubmitMock).not.toHaveBeenCalled();
  });

  it("should disable submit", async () => {
    const user = userEvent.setup();
    render(<ChatInput disabled onSubmit={onSubmitMock} />);

    const button = screen.getByRole("button");
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "Hello, world!");

    expect(button).toBeDisabled();
    await user.click(button);
    expect(onSubmitMock).not.toHaveBeenCalled();

    await user.keyboard("{Enter}");
    expect(onSubmitMock).not.toHaveBeenCalled();
  });

  it("should render a placeholder", () => {
    render(
      <ChatInput placeholder="Enter your message" onSubmit={onSubmitMock} />,
    );

    const textarea = screen.getByPlaceholderText("Enter your message");
    expect(textarea).toBeInTheDocument();
  });

  it("should create a newline instead of submitting when shift + enter is pressed", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Shift>} {Enter}"); // Shift + Enter

    expect(onSubmitMock).not.toHaveBeenCalled();
    // expect(textarea).toHaveValue("Hello, world!\n");
  });

  it("should clear the input message after sending a message", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");
    const button = screen.getByRole("button");

    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Enter}");
    expect(textarea).toHaveValue("");

    await user.type(textarea, "Hello, world!");
    await user.click(button);
    expect(textarea).toHaveValue("");
  });

  // NOTE: Functionality is already implemented but the test is not written
  it.todo("should dynamically increase the height of the textarea");
});
