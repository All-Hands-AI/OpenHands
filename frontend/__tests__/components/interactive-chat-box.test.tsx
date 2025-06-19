import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { InteractiveChatBox } from "#/components/features/chat/interactive-chat-box";

describe("InteractiveChatBox", () => {
  const onSubmitMock = vi.fn();
  const onStopMock = vi.fn();

  beforeAll(() => {
    global.URL.createObjectURL = vi
      .fn()
      .mockReturnValue("blob:http://example.com");
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render", () => {
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />);

    const chatBox = screen.getByTestId("interactive-chat-box");
    within(chatBox).getByTestId("chat-input");
    within(chatBox).getByTestId("upload-image-input");
  });

  it.fails("should set custom values", () => {
    render(
      <InteractiveChatBox
        onSubmit={onSubmitMock}
        onStop={onStopMock}
        value="Hello, world!"
      />,
    );

    const chatBox = screen.getByTestId("interactive-chat-box");
    const chatInput = within(chatBox).getByTestId("chat-input");

    expect(chatInput).toHaveValue("Hello, world!");
  });

  it("should display the image previews when images are uploaded", async () => {
    const user = userEvent.setup();
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />);

    const file = new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" });
    const input = screen.getByTestId("upload-image-input");

    expect(screen.queryAllByTestId("image-preview")).toHaveLength(0);

    await user.upload(input, file);
    expect(screen.queryAllByTestId("image-preview")).toHaveLength(1);

    const files = [
      new File(["(⌐□_□)"], "chucknorris2.png", { type: "image/png" }),
      new File(["(⌐□_□)"], "chucknorris3.png", { type: "image/png" }),
    ];

    await user.upload(input, files);
    expect(screen.queryAllByTestId("image-preview")).toHaveLength(3);
  });

  it("should remove the image preview when the close button is clicked", async () => {
    const user = userEvent.setup();
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />);

    const file = new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" });
    const input = screen.getByTestId("upload-image-input");

    await user.upload(input, file);
    expect(screen.queryAllByTestId("image-preview")).toHaveLength(1);

    const imagePreview = screen.getByTestId("image-preview");
    const closeButton = within(imagePreview).getByRole("button");
    await user.click(closeButton);

    expect(screen.queryAllByTestId("image-preview")).toHaveLength(0);
  });

  it("should call onSubmit with the message and images", async () => {
    const user = userEvent.setup();
    render(<InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />);

    const textarea = within(screen.getByTestId("chat-input")).getByRole(
      "textbox",
    );
    const input = screen.getByTestId("upload-image-input");
    const file = new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" });

    await user.upload(input, file);
    await user.type(textarea, "Hello, world!");
    await user.keyboard("{Enter}");

    expect(onSubmitMock).toHaveBeenCalledWith("Hello, world!", [file], []);

    // clear images after submission
    expect(screen.queryAllByTestId("image-preview")).toHaveLength(0);
  });

  it("should disable the submit button", async () => {
    const user = userEvent.setup();
    render(
      <InteractiveChatBox
        isDisabled
        onSubmit={onSubmitMock}
        onStop={onStopMock}
      />,
    );

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();

    await user.click(button);
    expect(onSubmitMock).not.toHaveBeenCalled();
  });

  it("should display the stop button if set and call onStop when clicked", async () => {
    const user = userEvent.setup();
    render(
      <InteractiveChatBox
        mode="stop"
        onSubmit={onSubmitMock}
        onStop={onStopMock}
      />,
    );

    const stopButton = screen.getByTestId("stop-button");
    expect(stopButton).toBeInTheDocument();

    await user.click(stopButton);
    expect(onStopMock).toHaveBeenCalledOnce();
  });

  it("should handle image upload and message submission correctly", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onStop = vi.fn();
    const onChange = vi.fn();

    const { rerender } = render(
      <InteractiveChatBox
        onSubmit={onSubmit}
        onStop={onStop}
        onChange={onChange}
        value="test message"
      />,
    );

    // Upload an image via the upload button - this should NOT clear the text input
    const file = new File(["dummy content"], "test.png", { type: "image/png" });
    const input = screen.getByTestId("upload-image-input");
    await user.upload(input, file);

    // Verify text input was not cleared
    expect(screen.getByRole("textbox")).toHaveValue("test message");
    expect(onChange).not.toHaveBeenCalledWith("");

    // Submit the message with image
    const submitButton = screen.getByRole("button", { name: "BUTTON$SEND" });
    await user.click(submitButton);

    // Verify onSubmit was called with the message and image
    expect(onSubmit).toHaveBeenCalledWith("test message", [file], []);

    // Verify onChange was called to clear the text input
    expect(onChange).toHaveBeenCalledWith("");

    // Simulate parent component updating the value prop
    rerender(
      <InteractiveChatBox
        onSubmit={onSubmit}
        onStop={onStop}
        onChange={onChange}
        value=""
      />,
    );

    // Verify the text input was cleared
    expect(screen.getByRole("textbox")).toHaveValue("");

    // Upload another image - this should NOT clear the text input
    onChange.mockClear();
    await user.upload(input, file);

    // Verify text input is still empty and onChange was not called
    expect(screen.getByRole("textbox")).toHaveValue("");
    expect(onChange).not.toHaveBeenCalled();
  });
});
