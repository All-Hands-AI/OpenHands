import React from "react";
import BaseModal from "../base-modal/BaseModal";
import { clearMsgs, fetchMsgs } from "../../../services/session";
import { sendChatMessageFromEvent } from "../../../services/chatService";
import { handleAssistantMessage } from "../../../services/actions";
import toast from "../../../utils/toast";

interface LoadPreviousSessionModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function LoadPreviousSessionModal({
  isOpen,
  onOpenChange,
}: LoadPreviousSessionModalProps) {
  const onStartNewSession = async () => {
    await clearMsgs();
  };

  const onResumeSession = async () => {
    try {
      const { messages } = await fetchMsgs();

      messages.forEach((message) => {
        if (message.role === "user") {
          sendChatMessageFromEvent(message.payload);
        }

        if (message.role === "assistant") {
          handleAssistantMessage(message.payload);
        }
      });
    } catch (error) {
      toast.stickyError("ws", "Error fetching the session");
    }
  };

  return (
    <BaseModal
      isOpen={isOpen}
      title="Unfinished Session Detected"
      onOpenChange={onOpenChange}
      actions={[
        {
          label: "Resume Session",
          className: "bg-primary rounded-small",
          action: onResumeSession,
          closeAfterAction: true,
        },
        {
          label: "Start New Session",
          className: "bg-neutral-500 rounded-small",
          action: onStartNewSession,
          closeAfterAction: true,
        },
      ]}
    >
      <p>
        You seem to have an unfinished task. Would you like to pick up where you
        left off or start fresh?
      </p>
    </BaseModal>
  );
}

export default LoadPreviousSessionModal;
