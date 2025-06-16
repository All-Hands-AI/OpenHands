import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useWsClient } from "#/context/ws-client-provider";
import { createUserFeedback } from "#/services/chat-service";
import { useConfig } from "#/hooks/query/use-config";
import StarIcon from "#/icons/star.svg?react";
import StarFilledIcon from "#/icons/star-filled.svg?react";
import { I18nKey } from "#/i18n/declaration";

interface FinishActionRatingProps {
  messageId: number;
}

// List of reasons for negative feedback with their translation keys
const FEEDBACK_REASONS = [
  { key: I18nKey.FEEDBACK$REASON_NOT_FOLLOW_INSTRUCTION },
  { key: I18nKey.FEEDBACK$REASON_BAD_SOLUTION },
  { key: I18nKey.FEEDBACK$REASON_LACKS_ACCESS },
];

export function FinishActionRating({ messageId }: FinishActionRatingProps) {
  const { t } = useTranslation();
  const { send } = useWsClient();
  const { data: config } = useConfig();
  const [rating, setRating] = useState<number | null>(null);
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);
  const [showReasons, setShowReasons] = useState(false);
  const [reasonTimeout, setReasonTimeout] = useState<NodeJS.Timeout | null>(
    null,
  );

  // Clean up timeout on unmount
  useEffect(
    () => () => {
      if (reasonTimeout) {
        clearTimeout(reasonTimeout);
      }
    },
    [reasonTimeout],
  );

  // Submit feedback to the backend
  const submitFeedback = (ratingValue: number, reason: string | null) => {
    // Convert rating to positive/negative
    const feedbackType = ratingValue >= 3 ? "positive" : "negative";

    // Send feedback event
    if (send) {
      send(
        createUserFeedback(
          feedbackType,
          "message",
          messageId,
          ratingValue,
          reason,
        ),
      );
    }

    // Hide reasons after submission
    setShowReasons(false);
  };

  // Handle rating selection
  const handleRatingClick = (value: number) => {
    setRating(value);
    setShowReasons(true);

    // Set a timeout to automatically submit feedback if no reason is selected
    const timeout = setTimeout(() => {
      submitFeedback(value, null);
    }, 3000);

    setReasonTimeout(timeout);
  };

  // Handle reason selection
  const handleReasonClick = (reason: string) => {
    if (reasonTimeout) {
      clearTimeout(reasonTimeout);
    }
    submitFeedback(rating!, reason);
  };

  // Only show in SAAS mode
  if (config?.APP_MODE !== "saas") {
    return null;
  }

  return (
    <div className="mt-2">
      {/* Rating stars */}
      <div className="flex items-center mb-2">
        <span className="text-sm mr-2">{t("FEEDBACK$RATE_RESPONSE")}</span>
        <div className="flex">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              type="button"
              key={value}
              className="p-1 focus:outline-none"
              onMouseEnter={() => setHoveredRating(value)}
              onMouseLeave={() => setHoveredRating(null)}
              onClick={() => handleRatingClick(value)}
              disabled={rating !== null}
            >
              {(hoveredRating !== null && value <= hoveredRating) ||
              (rating !== null && value <= rating) ? (
                <StarFilledIcon className="w-5 h-5 text-yellow-400" />
              ) : (
                <StarIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Reason selection */}
      {showReasons && (
        <div className="mt-2 bg-neutral-800 p-2 rounded">
          <p className="text-sm mb-2">{t("FEEDBACK$SELECT_REASON")}</p>
          <div className="flex flex-col gap-2">
            {FEEDBACK_REASONS.map((reason) => (
              <button
                type="button"
                key={reason.key}
                className="text-sm text-left p-2 hover:bg-neutral-700 rounded"
                onClick={() => handleReasonClick(t(reason.key))}
              >
                {t(reason.key)}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
