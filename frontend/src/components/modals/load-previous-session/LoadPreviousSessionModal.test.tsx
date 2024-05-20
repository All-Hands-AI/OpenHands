import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoadPreviousSessionModal from "./LoadPreviousSessionModal";
import { addChatMessageFromEvent } from "../../../services/chatService";
import { handleAssistantMessage } from "../../../services/actions";

const RESUME_SESSION_BUTTON_LABEL_KEY =
  "LOAD_SESSION$RESUME_SESSION_MODAL_ACTION_LABEL";
const START_NEW_SESSION_BUTTON_LABEL_KEY =
  "LOAD_SESSION$START_NEW_SESSION_MODAL_ACTION_LABEL";

vi.mock("../../../services/chatService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../services/chatService")>()),
  addChatMessageFromEvent: vi.fn(),
}));

vi.mock("../../../services/actions", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../services/actions")>()),
  handleAssistantMessage: vi.fn(),
}));

describe("LoadPreviousSession", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render two buttons", () => {
    render(<LoadPreviousSessionModal isOpen onOpenChange={vi.fn} />);

    screen.getByRole("button", { name: START_NEW_SESSION_BUTTON_LABEL_KEY });
    screen.getByRole("button", { name: RESUME_SESSION_BUTTON_LABEL_KEY });
  });

  it.skip("should clear messages if user chooses to start a new session", () => {
    const onOpenChangeMock = vi.fn();
    render(<LoadPreviousSessionModal isOpen onOpenChange={onOpenChangeMock} />);

    const startNewSessionButton = screen.getByRole("button", {
      name: START_NEW_SESSION_BUTTON_LABEL_KEY,
    });

    act(() => {
      userEvent.click(startNewSessionButton);
    });

    // modal should close right after clearing messages
    expect(onOpenChangeMock).toHaveBeenCalledWith(false);
  });

  it.skip("should load previous messages if user chooses to resume session", async () => {
    const onOpenChangeMock = vi.fn();
    render(<LoadPreviousSessionModal isOpen onOpenChange={onOpenChangeMock} />);

    const resumeSessionButton = screen.getByRole("button", {
      name: RESUME_SESSION_BUTTON_LABEL_KEY,
    });

    act(() => {
      userEvent.click(resumeSessionButton);
    });

    await waitFor(() => {
      expect(addChatMessageFromEvent).toHaveBeenCalledTimes(1);
      expect(handleAssistantMessage).toHaveBeenCalledTimes(1);
    });
    // modal should close right after fetching messages
    expect(onOpenChangeMock).toHaveBeenCalledWith(false);
  });

  it.skip("should show an error toast if there is an error fetching the session", async () => {
    render(<LoadPreviousSessionModal isOpen onOpenChange={vi.fn} />);

    const resumeSessionButton = screen.getByRole("button", {
      name: RESUME_SESSION_BUTTON_LABEL_KEY,
    });

    act(() => {
      userEvent.click(resumeSessionButton);
    });

    await waitFor(async () => {
      expect(handleAssistantMessage).not.toHaveBeenCalled();
      expect(addChatMessageFromEvent).not.toHaveBeenCalled();
      // error toast should be shown
      /*
      expect(toast.error).toHaveBeenCalledWith(
        "ws",
        "Error fetching the session",
      );
      */
    });
  });
});
