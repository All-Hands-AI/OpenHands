import React from "react";
import { CopyToClipboardButton } from "#/components/shared/buttons/copy-to-clipboard-button";
import { MessageFeedback } from "./message-feedback";

interface MessageActionsProps {
  messageId?: number;
  feedback?: "positive" | "negative" | null;
  isHovering: boolean;
  isCopy: boolean;
  onCopy: () => void;
}

export function MessageActions({
  messageId,
  feedback,
  isHovering,
  isCopy,
  onCopy,
}: MessageActionsProps) {
  return (
    <div
      className={`absolute top-1 right-1 flex items-center gap-1 ${!isHovering ? "hidden" : ""}`}
    >
      {messageId && (
        <MessageFeedback messageId={messageId} feedback={feedback} />
      )}
      <CopyToClipboardButton
        isHidden={!isHovering}
        isDisabled={isCopy}
        onClick={onCopy}
        mode={isCopy ? "copied" : "copy"}
      />
    </div>
  );
}
