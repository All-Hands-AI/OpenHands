import userEvent from "@testing-library/user-event";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, afterEach, vi, it, expect } from "vitest";
import { ChatInput } from "#/components/features/chat/chat-input";

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

  it("should not call onSubmit when the message is only whitespace", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "   ");
    await user.keyboard("{Enter}");

    expect(onSubmitMock).not.toHaveBeenCalled();

    await user.type(textarea, " \t\n");
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

  it("should render a placeholder with translation key", () => {
    render(<ChatInput onSubmit={onSubmitMock} />);

    const textarea = screen.getByPlaceholderText("SUGGESTIONS$WHAT_TO_BUILD");
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

  it("should hide the submit button", () => {
    render(<ChatInput onSubmit={onSubmitMock} showButton={false} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("should call onChange when the user types", async () => {
    const user = userEvent.setup();
    const onChangeMock = vi.fn();
    render(<ChatInput onSubmit={onSubmitMock} onChange={onChangeMock} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "Hello, world!");

    expect(onChangeMock).toHaveBeenCalledTimes("Hello, world!".length);
  });

  it("should have set the passed value", () => {
    render(<ChatInput value="Hello, world!" onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");

    expect(textarea).toHaveValue("Hello, world!");
  });

  it("should display the stop button and trigger the callback", async () => {
    const user = userEvent.setup();
    const onStopMock = vi.fn();
    render(
      <ChatInput onSubmit={onSubmitMock} button="stop" onStop={onStopMock} />,
    );
    const stopButton = screen.getByTestId("stop-button");

    await user.click(stopButton);
    expect(onStopMock).toHaveBeenCalledOnce();
  });

  it("should call onFocus and onBlur when the textarea is focused and blurred", async () => {
    const user = userEvent.setup();
    const onFocusMock = vi.fn();
    const onBlurMock = vi.fn();
    render(
      <ChatInput
        onSubmit={onSubmitMock}
        onFocus={onFocusMock}
        onBlur={onBlurMock}
      />,
    );
    const textarea = screen.getByRole("textbox");

    await user.click(textarea);
    expect(onFocusMock).toHaveBeenCalledOnce();

    await user.tab();
    expect(onBlurMock).toHaveBeenCalledOnce();
  });

  it("should handle text paste correctly", () => {
    const onSubmit = vi.fn();
    const onChange = vi.fn();

    render(<ChatInput onSubmit={onSubmit} onChange={onChange} />);

    const input = screen.getByTestId("chat-input").querySelector("textarea");
    expect(input).toBeTruthy();

    // Fire paste event with text data
    fireEvent.paste(input!, {
      clipboardData: {
        getData: (type: string) => (type === "text/plain" ? "test paste" : ""),
        files: [],
      },
    });
  });

  it("should handle image paste correctly", () => {
    const onSubmit = vi.fn();
    const onImagePaste = vi.fn();

    render(<ChatInput onSubmit={onSubmit} onImagePaste={onImagePaste} />);

    const input = screen.getByTestId("chat-input").querySelector("textarea");
    expect(input).toBeTruthy();

    // Create a paste event with an image file
    const file = new File(["dummy content"], "image.png", {
      type: "image/png",
    });

    // Fire paste event with image data
    fireEvent.paste(input!, {
      clipboardData: {
        getData: () => "",
        files: [file],
      },
    });

    // Verify image paste was handled
    expect(onImagePaste).toHaveBeenCalledWith([file]);
  });

  it("should not submit when Enter is pressed during IME composition", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSubmit={onSubmitMock} />);
    const textarea = screen.getByRole("textbox");

    await user.type(textarea, "こんにちは");

    // Simulate Enter during IME composition
    fireEvent.keyDown(textarea, {
      key: "Enter",
      isComposing: true,
      nativeEvent: { isComposing: true },
    });

    expect(onSubmitMock).not.toHaveBeenCalled();

    // Simulate normal Enter after composition is done
    fireEvent.keyDown(textarea, {
      key: "Enter",
      isComposing: false,
      nativeEvent: { isComposing: false },
    });

    expect(onSubmitMock).toHaveBeenCalledWith("こんにちは");
  });
});
