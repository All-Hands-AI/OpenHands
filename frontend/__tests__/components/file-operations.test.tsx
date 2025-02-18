import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Messages } from "#/components/features/chat/messages";
import type { Message } from "#/message";

describe("File Operations Messages", () => {
  it("should show success indicator for successful file read operation", () => {
    const messages: Message[] = [
      {
        type: "action",
        translationID: "read_file_contents",
        content: "Successfully read file contents",
        success: true,
        sender: "assistant",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

    const statusIcon = screen.getByTestId("status-icon");
    expect(statusIcon).toBeInTheDocument();
    expect(statusIcon.closest("svg")).toHaveClass("fill-success");
  });

  it("should show failure indicator for failed file read operation", () => {
    const messages: Message[] = [
      {
        type: "action",
        translationID: "read_file_contents",
        content: "Failed to read file contents",
        success: false,
        sender: "assistant",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

    const statusIcon = screen.getByTestId("status-icon");
    expect(statusIcon).toBeInTheDocument();
    expect(statusIcon.closest("svg")).toHaveClass("fill-danger");
  });

  it("should show success indicator for successful file edit operation", () => {
    const messages: Message[] = [
      {
        type: "action",
        translationID: "edit_file_contents",
        content: "Successfully edited file contents",
        success: true,
        sender: "assistant",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

    const statusIcon = screen.getByTestId("status-icon");
    expect(statusIcon).toBeInTheDocument();
    expect(statusIcon.closest("svg")).toHaveClass("fill-success");
  });

  it("should show failure indicator for failed file edit operation", () => {
    const messages: Message[] = [
      {
        type: "action",
        translationID: "edit_file_contents",
        content: "Failed to edit file contents",
        success: false,
        sender: "assistant",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

    const statusIcon = screen.getByTestId("status-icon");
    expect(statusIcon).toBeInTheDocument();
    expect(statusIcon.closest("svg")).toHaveClass("fill-danger");
  });
});
