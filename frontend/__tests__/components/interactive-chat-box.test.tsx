import { render, screen, within, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { InteractiveChatBox } from "#/components/features/chat/interactive-chat-box";
import { renderWithProviders } from "../../test-utils";
import { AgentState } from "#/types/agent-state";

// Mock the useActiveConversation hook
vi.mock("#/hooks/query/use-active-conversation", () => ({
  useActiveConversation: () => ({
    data: { status: null },
    isFetched: true,
    refetch: vi.fn(),
  }),
}));

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
    renderWithProviders(
      <InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.INIT,
          },
        },
      },
    );

    const chatBox = screen.getByTestId("interactive-chat-box");
    expect(chatBox).toBeInTheDocument();
  });

  it("should set custom values", () => {
    renderWithProviders(
      <InteractiveChatBox
        onSubmit={onSubmitMock}
        onStop={onStopMock}
        value="Hello, world!"
      />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.AWAITING_USER_INPUT,
          },
        },
      },
    );

    const textbox = screen.getByTestId("chat-input");
    expect(textbox).toHaveTextContent("Hello, world!");
  });

  it("should display the image previews when images are uploaded", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.INIT,
          },
        },
      },
    );

    // Create a larger file to ensure it passes validation
    const fileContent = new Array(1024).fill("a").join(""); // 1KB file
    const file = new File([fileContent], "chucknorris.png", {
      type: "image/png",
    });

    // Click on the paperclip icon to trigger file selection
    const paperclipIcon = screen.getByTestId("paperclip-icon");
    await user.click(paperclipIcon);

    // Now trigger the file input change event directly
    const input = screen.getByTestId("upload-image-input");
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.queryAllByTestId("image-preview")).toHaveLength(1);
  });

  it("should remove the image preview when the close button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.INIT,
          },
        },
      },
    );

    const fileContent = new Array(1024).fill("a").join(""); // 1KB file
    const file = new File([fileContent], "chucknorris.png", {
      type: "image/png",
    });

    // Click on the paperclip icon to trigger file selection
    const paperclipIcon = screen.getByTestId("paperclip-icon");
    await user.click(paperclipIcon);

    const input = screen.getByTestId("upload-image-input");
    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.queryAllByTestId("image-preview")).toHaveLength(1);

    const imagePreview = screen.getByTestId("image-preview");
    const closeButton = within(imagePreview).getByRole("button");
    await user.click(closeButton);

    expect(screen.queryAllByTestId("image-preview")).toHaveLength(0);
  });

  it("should call onSubmit with the message and images", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.INIT,
          },
        },
      },
    );

    const textarea = screen.getByTestId("chat-input");
    const fileContent = new Array(1024).fill("a").join(""); // 1KB file
    const file = new File([fileContent], "chucknorris.png", {
      type: "image/png",
    });

    // Click on the paperclip icon to trigger file selection
    const paperclipIcon = screen.getByTestId("paperclip-icon");
    await user.click(paperclipIcon);

    const input = screen.getByTestId("upload-image-input");
    fireEvent.change(input, { target: { files: [file] } });

    // Type the message and ensure it's properly set
    await user.type(textarea, "Hello, world!");

    // Verify the text is in the input before submitting
    expect(textarea).toHaveTextContent("Hello, world!");

    // Ensure the text content is properly set in the contenteditable div
    fireEvent.input(textarea, { target: { textContent: "Hello, world!" } });

    // Also set the textContent directly to ensure it's available for innerText
    textarea.textContent = "Hello, world!";

    // Trigger input event to ensure the component updates properly
    fireEvent.input(textarea, { target: { innerText: "Hello, world!" } });

    // Click the submit button instead of pressing Enter for more reliable testing
    const submitButton = screen.getByTestId("submit-button");

    // Verify the button is enabled before clicking
    expect(submitButton).not.toBeDisabled();

    await user.click(submitButton);

    expect(onSubmitMock).toHaveBeenCalledWith("Hello, world!", [file], []);

    // clear images after submission
    expect(screen.queryAllByTestId("image-preview")).toHaveLength(0);
  });

  it("should disable the submit button when agent is loading", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.LOADING,
          },
        },
      },
    );

    const button = screen.getByTestId("submit-button");
    expect(button).toBeDisabled();

    await user.click(button);
    expect(onSubmitMock).not.toHaveBeenCalled();
  });

  it("should display the stop button when agent is running and call onStop when clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <InteractiveChatBox onSubmit={onSubmitMock} onStop={onStopMock} />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.RUNNING,
          },
        },
      },
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

    const { rerender } = renderWithProviders(
      <InteractiveChatBox
        onSubmit={onSubmit}
        onStop={onStop}
        value="test message"
      />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.AWAITING_USER_INPUT,
          },
        },
      },
    );

    // Upload an image via the upload button - this should NOT clear the text input
    const fileContent = new Array(1024).fill("a").join(""); // 1KB file
    const file = new File([fileContent], "test.png", { type: "image/png" });

    // Click on the paperclip icon to trigger file selection
    const paperclipIcon = screen.getByTestId("paperclip-icon");
    await user.click(paperclipIcon);

    const input = screen.getByTestId("upload-image-input");
    fireEvent.change(input, { target: { files: [file] } });

    // Verify text input was not cleared
    expect(screen.getByTestId("chat-input")).toHaveTextContent("test message");

    // Ensure innerText is properly set for the contenteditable div
    const textarea = screen.getByTestId("chat-input");

    fireEvent.input(textarea, { target: { innerText: "test message" } });

    // Submit the message with image
    const submitButton = screen.getByTestId("submit-button");
    await user.click(submitButton);

    // Verify onSubmit was called with the message and image
    expect(onSubmit).toHaveBeenCalledWith("test message", [file], []);

    // Simulate parent component updating the value prop
    rerender(
      <InteractiveChatBox onSubmit={onSubmit} onStop={onStop} value="" />,
    );

    // Verify the text input was cleared
    expect(screen.getByTestId("chat-input")).toHaveTextContent("");

    // Upload another image - this should NOT clear the text input
    await user.click(paperclipIcon);
    fireEvent.change(input, { target: { files: [file] } });

    // Verify text input is still empty
    expect(screen.getByTestId("chat-input")).toHaveTextContent("");
  });
});
