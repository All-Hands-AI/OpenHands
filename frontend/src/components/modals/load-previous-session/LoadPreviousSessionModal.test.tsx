import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoadPreviousSessionModal from "./LoadPreviousSessionModal";
import { clearMsgs, fetchMsgs } from "../../../services/session";
import { sendChatMessageFromEvent } from "../../../services/chatService";
import { handleAssistantMessage } from "../../../services/actions";
import toast from "../../../utils/toast";

const RESUME_SESSION_BUTTON_LABEL_KEY =
  "LOAD_SESSION$RESUME_SESSION_MODAL_ACTION_LABEL";
const START_NEW_SESSION_BUTTON_LABEL_KEY =
  "LOAD_SESSION$START_NEW_SESSION_MODAL_ACTION_LABEL";

const mocks = vi.hoisted(() => ({
  fetchMsgsMock: vi.fn(),
}));

vi.mock("../../../services/session", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../services/session")>()),
  clearMsgs: vi.fn(),
  fetchMsgs: mocks.fetchMsgsMock.mockResolvedValue({
    messages: [
      {
        id: "1",
        role: "user",
        payload: { type: "action" },
      },
      {
        id: "2",
        role: "assistant",
        payload: { type: "observation" },
      },
    ],
  }),
}));

vi.mock("../../../services/chatService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../services/chatService")>()),
  sendChatMessageFromEvent: vi.fn(),
}));

vi.mock("../../../services/actions", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../services/actions")>()),
  handleAssistantMessage: vi.fn(),
}));

vi.mock("../../../utils/toast", () => ({
  default: {
    stickyError: vi.fn(),
  },
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

  it("should clear messages if user chooses to start a new session", () => {
    const onOpenChangeMock = vi.fn();
    render(<LoadPreviousSessionModal isOpen onOpenChange={onOpenChangeMock} />);

    const startNewSessionButton = screen.getByRole("button", {
      name: START_NEW_SESSION_BUTTON_LABEL_KEY,
    });

    act(() => {
      userEvent.click(startNewSessionButton);
    });

    expect(clearMsgs).toHaveBeenCalledTimes(1);
    // modal should close right after clearing messages
    expect(onOpenChangeMock).toHaveBeenCalledWith(false);
  });

  it("should load previous messages if user chooses to resume session", async () => {
    const onOpenChangeMock = vi.fn();
    render(<LoadPreviousSessionModal isOpen onOpenChange={onOpenChangeMock} />);

    const resumeSessionButton = screen.getByRole("button", {
      name: RESUME_SESSION_BUTTON_LABEL_KEY,
    });

    act(() => {
      userEvent.click(resumeSessionButton);
    });

    await waitFor(() => {
      expect(fetchMsgs).toHaveBeenCalledTimes(1);
      expect(sendChatMessageFromEvent).toHaveBeenCalledTimes(1);
      expect(handleAssistantMessage).toHaveBeenCalledTimes(1);
    });
    // modal should close right after fetching messages
    expect(onOpenChangeMock).toHaveBeenCalledWith(false);
  });

  it("should show an error toast if there is an error fetching the session", async () => {
    mocks.fetchMsgsMock.mockRejectedValue(new Error("Get messages failed."));

    render(<LoadPreviousSessionModal isOpen onOpenChange={vi.fn} />);

    const resumeSessionButton = screen.getByRole("button", {
      name: RESUME_SESSION_BUTTON_LABEL_KEY,
    });

    act(() => {
      userEvent.click(resumeSessionButton);
    });

    await waitFor(async () => {
      await expect(() => fetchMsgs()).rejects.toThrow();
      expect(handleAssistantMessage).not.toHaveBeenCalled();
      expect(sendChatMessageFromEvent).not.toHaveBeenCalled();
      // error toast should be shown
      expect(toast.stickyError).toHaveBeenCalledWith(
        "ws",
        "Error fetching the session",
      );
    });
  });
});
