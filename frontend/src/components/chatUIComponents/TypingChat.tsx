import React, { ReactNode } from "react";
import { useSelector } from "react-redux";
import { Card, CardBody } from "@nextui-org/react";
import { RootState } from "../../store";
import { useTypingEffect } from "../../hooks/useTypingEffect";
import {
  addAssistantMessageToChat,
  setCurrentQueueMarkerState,
  setTypingAcitve,
} from "../../services/chatService";

/**
 * @returns jsx
 *
 * component used for typing effect when assistant replies
 *
 * makes uses of useTypingEffect hook
 *
 */
function TypingChat() {
  const { currentTypingMessage, currentQueueMarker, queuedTyping, messages } =
    useSelector((state: RootState) => state.chat);

  const messageContent = useTypingEffect([currentTypingMessage], {
    loop: false,
    setTypingAcitve,
    setCurrentQueueMarkerState,
    currentQueueMarker,
    playbackRate: 0.1,
    addAssistantMessageToChat,
    assistantMessageObj: messages?.[queuedTyping[currentQueueMarker]],
  });

  return (
    currentQueueMarker !== null && (
      <Card className="bg-success-100">
        <CardBody>{messageContent}</CardBody>
      </Card>
    )
  );
}

export default TypingChat;
