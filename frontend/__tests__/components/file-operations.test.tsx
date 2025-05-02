import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Messages } from "#/components/features/chat/messages";
import type { Message } from "#/message";
import { renderWithProviders } from "test-utils";

// Mock the useParams hook to provide a conversationId
vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useParams: () => ({ conversationId: "test-conversation-id" }),
  };
});

// Mock react-i18next
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: {
        changeLanguage: () => new Promise(() => {}),
        language: "en",
        exists: () => true,
        isInitialized: true,
        on: vi.fn(),
        off: vi.fn(),
      },
    }),
  };
});

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

    renderWithProviders(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

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

    renderWithProviders(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

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

    renderWithProviders(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

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

    renderWithProviders(<Messages messages={messages} isAwaitingUserConfirmation={false} />);

    const statusIcon = screen.getByTestId("status-icon");
    expect(statusIcon).toBeInTheDocument();
    expect(statusIcon.closest("svg")).toHaveClass("fill-danger");
  });
});
