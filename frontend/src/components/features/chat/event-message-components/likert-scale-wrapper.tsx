import React from "react";
import { LikertScale } from "../../feedback/likert-scale";

interface LikertScaleWrapperProps {
  shouldShow?: boolean;
  eventId?: string;
  config?: { APP_MODE?: string } | null;
  isCheckingFeedback: boolean;
  feedbackData: {
    exists: boolean;
    rating?: number;
    reason?: string;
  };
}

export function LikertScaleWrapper({
  shouldShow,
  eventId,
  config,
  isCheckingFeedback,
  feedbackData,
}: LikertScaleWrapperProps) {
  if (config?.APP_MODE !== "saas" || isCheckingFeedback) {
    return null;
  }

  if (!shouldShow) {
    return null;
  }

  return (
    <LikertScale
      eventId={eventId}
      initiallySubmitted={feedbackData.exists}
      initialRating={feedbackData.rating}
      initialReason={feedbackData.reason}
    />
  );
}
