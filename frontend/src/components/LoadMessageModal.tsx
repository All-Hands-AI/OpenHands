import React from "react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
} from "@nextui-org/react";
import { fetchMsgs, clearMsgs } from "../services/session";
import { sendChatMessageFromEvent } from "../services/chatService";
import { handleAssistantMessage } from "../services/actions";
import { ResFetchMsg } from "../types/ResponseType";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

function LoadMessageModal({ isOpen, onClose }: Props): JSX.Element {
  const handleDelMsg = () => {
    clearMsgs().then().catch();
    onClose();
  };

  const handleLoadMsg = () => {
    fetchMsgs()
      .then((data) => {
        if (
          data === undefined ||
          data.messages === undefined ||
          data.messages.length === 0
        ) {
          return;
        }
        const { messages } = data;
        messages.forEach((msg: ResFetchMsg) => {
          switch (msg.role) {
            case "user":
              sendChatMessageFromEvent(msg.payload);
              break;
            case "assistant":
              handleAssistantMessage(msg.payload);
              break;
            default:
          }
        });
      })
      .catch();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} hideCloseButton backdrop="blur">
      <ModalContent>
        <>
          <ModalHeader className="flex flex-col gap-1">
            Unfinished Session Detected
          </ModalHeader>
          <ModalBody>
            You have an unfinished session. Do you want to load it?
          </ModalBody>

          <ModalFooter>
            <Button color="danger" variant="light" onPress={handleDelMsg}>
              No, start a new session
            </Button>
            <Button color="primary" onPress={handleLoadMsg}>
              Okay, load it
            </Button>
          </ModalFooter>
        </>
      </ModalContent>
    </Modal>
  );
}

export default LoadMessageModal;
