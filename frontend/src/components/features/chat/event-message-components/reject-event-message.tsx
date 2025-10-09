import React from "react";
import { ChatMessage } from "../chat-message";

interface RejectEventMessageProps {
  event: { message: string };
}

export function RejectEventMessage({ event }: RejectEventMessageProps) {
  return (
    <div>
      <ChatMessage type="agent" message={event.message} />
    </div>
  );
}
