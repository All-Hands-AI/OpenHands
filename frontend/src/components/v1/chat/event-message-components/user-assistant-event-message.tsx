import React from "react";
import { MessageEvent } from "#/types/v1/core";
import { ChatMessage } from "../../../features/chat/chat-message";
import { ImageCarousel } from "../../../features/images/image-carousel";
// TODO: Implement file_urls support for V1 messages
// import { FileList } from "../../../features/files/file-list";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { MicroagentStatusWrapper } from "../../../features/chat/event-message-components/microagent-status-wrapper";
// TODO: Implement V1 LikertScaleWrapper when API supports V1 event IDs
// import { LikertScaleWrapper } from "../../../features/chat/event-message-components/likert-scale-wrapper";
import { parseMessageFromEvent } from "../event-content-helpers/parse-message-from-event";
import { MicroagentStatus } from "#/types/microagent-status";

interface UserAssistantEventMessageProps {
  event: MessageEvent;
  shouldShowConfirmationButtons: boolean;
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
    tooltip?: string;
  }>;
}

export function UserAssistantEventMessage({
  event,
  shouldShowConfirmationButtons,
  microagentStatus,
  microagentConversationId,
  microagentPRUrl,
  actions,
}: UserAssistantEventMessageProps) {
  const message = parseMessageFromEvent(event);

  // Extract image URLs from the message content
  const imageUrls: string[] = [];
  if (Array.isArray(event.llm_message.content)) {
    event.llm_message.content.forEach((content) => {
      if (content.type === "image") {
        imageUrls.push(...content.image_urls);
      }
    });
  }

  return (
    <>
      <ChatMessage type={event.source} message={message} actions={actions}>
        {imageUrls.length > 0 && (
          <ImageCarousel size="small" images={imageUrls} />
        )}
        {/* TODO: Handle file_urls if V1 messages support them */}
        {shouldShowConfirmationButtons && <ConfirmationButtons />}
      </ChatMessage>
      <MicroagentStatusWrapper
        microagentStatus={microagentStatus}
        microagentConversationId={microagentConversationId}
        microagentPRUrl={microagentPRUrl}
        actions={actions}
      />
      {/* LikertScaleWrapper expects V0 event types, skip for now */}
    </>
  );
}
