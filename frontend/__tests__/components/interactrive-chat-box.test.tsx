import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

function InteractiveChatBox() {
  return (
    <div data-testid="interactive-chat-box">
      <div data-testid="chat-interface" />
      <div data-testid="upload-image-input" />
    </div>
  );
}

describe("InteractiveChatBox", () => {
  it("should render", () => {
    render(<InteractiveChatBox />);

    const chatBox = screen.getByTestId("interactive-chat-box");
    within(chatBox).getByTestId("chat-interface");
    within(chatBox).getByTestId("upload-image-input");
  });

  it("should display the image previews when images are uploaded", async () => {
    const user = userEvent.setup();
    render(<InteractiveChatBox />);

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
});
