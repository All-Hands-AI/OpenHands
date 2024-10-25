import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { InteractiveChatBox } from "#/components/interactive-chat-box";

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
});
