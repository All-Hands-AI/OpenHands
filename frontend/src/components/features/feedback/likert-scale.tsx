import React, { useState, useEffect } from "react";
import { cn } from "#/utils/utils";
import i18n from "#/i18n";

interface LikertScaleProps {
  onRatingSubmit: (rating: number, reason?: string) => void;
}

const FEEDBACK_REASONS = [
  "The agent did not follow my instruction",
  "The agent did not implement a good solution",
  "The agent lacks access to software or hardware that is not installable in the runtime to complete the task",
];

export function LikertScale({ onRatingSubmit }: LikertScaleProps) {
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [showReasons, setShowReasons] = useState(false);
  const [reasonTimeout, setReasonTimeout] = useState<NodeJS.Timeout | null>(
    null,
  );

  // Handle star rating selection
  const handleRatingClick = (rating: number) => {
    setSelectedRating(rating);
    setShowReasons(true);

    // Set a timeout to auto-submit if no reason is selected
    const timeout = setTimeout(() => {
      onRatingSubmit(rating);
      setShowReasons(false);
    }, 3000);

    setReasonTimeout(timeout);
  };

  // Handle reason selection
  const handleReasonClick = (reason: string) => {
    if (selectedRating && reasonTimeout) {
      clearTimeout(reasonTimeout);
      onRatingSubmit(selectedRating, reason);
      setShowReasons(false);
    }
  };

  // Clean up timeout on unmount
  useEffect(
    () => () => {
      if (reasonTimeout) {
        clearTimeout(reasonTimeout);
      }
    },
    [reasonTimeout],
  );

  return (
    <div className="mt-4 flex flex-col gap-2">
      <div className="text-sm text-gray-500 mb-1">
        {i18n.t("FEEDBACK$RATE_AGENT_PERFORMANCE")}
      </div>
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map((rating) => (
          <button
            type="button"
            key={rating}
            onClick={() => handleRatingClick(rating)}
            className={cn(
              "text-2xl transition-all",
              selectedRating && selectedRating >= rating
                ? "text-yellow-400"
                : "text-gray-300 hover:text-yellow-200",
            )}
            aria-label={`Rate ${rating} stars`}
          >
            ★
          </button>
        ))}
      </div>

      {showReasons && (
        <div className="mt-2 flex flex-col gap-2">
          <div className="text-sm text-gray-500 mb-1">
            {i18n.t("FEEDBACK$SELECT_REASON")}
          </div>
          <div className="flex flex-col gap-1">
            {FEEDBACK_REASONS.map((reason) => (
              <button
                type="button"
                key={reason}
                onClick={() => handleReasonClick(reason)}
                className="text-sm text-left py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                {reason}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
