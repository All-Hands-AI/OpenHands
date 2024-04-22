import React from "react";
import BaseModal from "../base-modal/BaseModal";
import { clearMsgs, fetchMsgs } from "../../services/session";
import { sendChatMessageFromEvent } from "../../services/chatService";
import { handleAssistantMessage } from "../../services/actions";
import toast from "../../utils/toast";

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
          action: onResumeSession,
          closeAfterAction: true,
        },
        {
          label: "Start New Session",
          action: onStartNewSession,
          closeAfterAction: true,
        },
      ]}
    />
  );
}

export default LoadPreviousSessionModal;
