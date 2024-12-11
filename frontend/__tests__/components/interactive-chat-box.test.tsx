import { render, screen, within, fireEvent } from "@testing-library/react";
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

    expect(onSubmitMock).toHaveBeenCalledWith("Hello, world!", [file]);

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

  it("should clear text input after image paste", async () => {
    const onSubmit = vi.fn();
    const onStop = vi.fn();
    const onChange = vi.fn();

    render(
      <InteractiveChatBox
        onSubmit={onSubmit}
        onStop={onStop}
        onChange={onChange}
        value="test message"
      />
    );

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("test message");

    // Create a mock image file
    const imageFile = new File(["dummy content"], "test.png", { type: "image/png" });
    const clipboardEvent = new Event("paste", { bubbles: true }) as any;
    clipboardEvent.clipboardData = {
      files: [imageFile],
      getData: () => "",
    };

    // Trigger paste event
    fireEvent(textarea, clipboardEvent);

    // The text input should be cleared via onChange
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("should clear text input after image drop", async () => {
    const onSubmit = vi.fn();
    const onStop = vi.fn();
    const onChange = vi.fn();

    render(
      <InteractiveChatBox
        onSubmit={onSubmit}
        onStop={onStop}
        onChange={onChange}
        value="test message"
      />
    );

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("test message");

    // Create a mock image file
    const imageFile = new File(["dummy content"], "test.png", { type: "image/png" });
    const dropEvent = new Event("drop", { bubbles: true }) as any;
    dropEvent.dataTransfer = {
      files: [imageFile],
      types: ["Files"],
    };
    dropEvent.preventDefault = vi.fn();

    // Trigger drop event
    fireEvent(textarea, dropEvent);

    // The text input should be cleared via onChange
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("should clear text input when uploading an image but not when removing it", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onStop = vi.fn();
    const onChange = vi.fn();

    render(
      <InteractiveChatBox
        onSubmit={onSubmit}
        onStop={onStop}
        onChange={onChange}
        value="test message"
      />
    );

    // Upload an image - this should clear the text input
    const file = new File(["dummy content"], "test.png", { type: "image/png" });
    const input = screen.getByTestId("upload-image-input");
    await user.upload(input, file);

    // Verify onChange was called to clear the text
    expect(onChange).toHaveBeenCalledWith("");
    onChange.mockClear();

    // Remove the image - this should not clear the text input
    const imagePreview = screen.getByTestId("image-preview");
    const closeButton = within(imagePreview).getByRole("button");
    await user.click(closeButton);

    // Verify onChange was not called again
    expect(onChange).not.toHaveBeenCalled();
  });
});
