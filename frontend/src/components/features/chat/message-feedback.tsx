import React from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { useWsClient } from "#/context/ws-client-provider";
import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";
import { createUserFeedback } from "#/services/chat-service";
import { setMessageFeedback } from "#/state/chat-slice";
import { I18nKey } from "#/i18n/declaration";

interface MessageFeedbackProps {
  messageId: number;
  feedback?: "positive" | "negative" | null;
}

export function MessageFeedback({ messageId, feedback }: MessageFeedbackProps) {
  const { t } = useTranslation();
  const { send } = useWsClient();
  const dispatch = useDispatch();

  const handleFeedback = (feedbackType: "positive" | "negative") => {
    // Don't send if already selected
    if (feedback === feedbackType) return;

    // Update local state
    dispatch(setMessageFeedback({ messageId, feedbackType }));

    // Send to backend
    send(createUserFeedback(feedbackType, "message", messageId));
  };

  return (
    <div className="flex gap-1 mt-2">
      <TrajectoryActionButton
        testId={`positive-${messageId}`}
        onClick={() => handleFeedback("positive")}
        icon={<ThumbsUpIcon width={15} height={15} />}
        tooltip={t(I18nKey.BUTTON$MARK_HELPFUL)}
        className={feedback === "positive" ? "bg-neutral-700" : ""}
      />
      <TrajectoryActionButton
        testId={`negative-${messageId}`}
        onClick={() => handleFeedback("negative")}
        icon={<ThumbDownIcon width={15} height={15} />}
        tooltip={t(I18nKey.BUTTON$MARK_NOT_HELPFUL)}
        className={feedback === "negative" ? "bg-neutral-700" : ""}
      />
    </div>
  );
}
