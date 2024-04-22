import React from "react";
import { Button } from "@nextui-org/react";
import { fetchMsgs, clearMsgs } from "#/services/session";
import { sendChatMessageFromEvent } from "#/services/chatService";
import { handleAssistantMessage } from "#/services/actions";
import { ResFetchMsg } from "#/types/ResponseType";
import toast from "#/utils/toast";
import ODModal from "./ODModal";

interface LoadMessageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function LoadMessageModal({
  isOpen,
  onClose,
}: LoadMessageModalProps): JSX.Element {
  const handleStartNewSession = () => {
    clearMsgs().then().catch();
    onClose();
  };

  const handleResumeSession = async () => {
    try {
      const data = await fetchMsgs();
      if (!data || !data.messages || data.messages.length === 0) {
        return;
      }

      data.messages.forEach((msg: ResFetchMsg) => {
        switch (msg.role) {
          case "user":
            sendChatMessageFromEvent(msg.payload);
            break;
          case "assistant":
            handleAssistantMessage(msg.payload);
            break;
          default:
            break;
        }
      });

      onClose();
    } catch (error) {
      toast.stickyError("ws", "Error fetching the session");
    }
  };

  return (
    <ODModal
      size="md"
      isOpen={isOpen}
      onClose={onClose}
      hideCloseButton
      backdrop="blur"
      title="Unfinished Session Detected"
      primaryAction={
        <Button
          className="bg-primary rounded-small"
          onPress={handleResumeSession}
        >
          Resume Session
        </Button>
      }
      secondaryAction={
        <Button
          className="bg-neutral-500 rounded-small"
          onPress={handleStartNewSession}
        >
          Start New Session
        </Button>
      }
    >
      <p>
        You seem to have an unfinished task. Would you like to pick up where you
        left off or start fresh?
      </p>
    </ODModal>
  );
}

export default LoadMessageModal;
