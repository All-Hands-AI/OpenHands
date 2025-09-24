import React from "react";
import { OpenHandsObservation } from "#/types/core/observations";
import { isRejectObservation } from "#/types/core/guards";
import { ChatMessage } from "../chat-message";

interface RejectEventMessageProps {
  event: OpenHandsObservation;
}

export function RejectEventMessage({ event }: RejectEventMessageProps) {
  if (!isRejectObservation(event)) {
    return null;
  }

  return (
    <div>
      <ChatMessage type="agent" message={event.content} />
    </div>
  );
}
