import React, { useState, useEffect } from "react";
import { cn } from "#/utils/utils";
import i18n from "#/i18n";

interface LikertScaleProps {
  onRatingSubmit: (rating: number, reason?: string) => void;
  initiallySubmitted?: boolean;
  initialRating?: number;
  initialReason?: string;
}

const FEEDBACK_REASONS = [
  i18n.t("FEEDBACK$REASON_MISUNDERSTOOD_INSTRUCTION"),
  i18n.t("FEEDBACK$REASON_FORGOT_CONTEXT"),
  i18n.t("FEEDBACK$REASON_UNNECESSARY_CHANGES"),
  i18n.t("FEEDBACK$REASON_OTHER"),
];

export function LikertScale({
  onRatingSubmit,
  initiallySubmitted = false,
  initialRating,
  initialReason,
}: LikertScaleProps) {
  const [selectedRating, setSelectedRating] = useState<number | null>(
    initialRating || null,
  );
  const [selectedReason, setSelectedReason] = useState<string | null>(
    initialReason || null,
  );
  const [showReasons, setShowReasons] = useState(false);
  const [reasonTimeout, setReasonTimeout] = useState<NodeJS.Timeout | null>(
    null,
  );
  const [isSubmitted, setIsSubmitted] = useState(initiallySubmitted);

  // Update isSubmitted if initiallySubmitted changes
  useEffect(() => {
    setIsSubmitted(initiallySubmitted);
  }, [initiallySubmitted]);

  // Update selectedRating if initialRating changes
  useEffect(() => {
    if (initialRating) {
      setSelectedRating(initialRating);
    }
  }, [initialRating]);

  // Update selectedReason if initialReason changes
  useEffect(() => {
    if (initialReason) {
      setSelectedReason(initialReason);
    }
  }, [initialReason]);

  // Submit feedback and disable the component
  const submitFeedback = (rating: number, reason?: string) => {
    onRatingSubmit(rating, reason);
    setSelectedReason(reason || null);
    setShowReasons(false);
    setIsSubmitted(true);
  };

  // Handle star rating selection
  const handleRatingClick = (rating: number) => {
    if (isSubmitted) return; // Prevent changes after submission

    setSelectedRating(rating);
    setShowReasons(true);

    // Set a timeout to auto-submit if no reason is selected
    const timeout = setTimeout(() => {
      submitFeedback(rating);
    }, 3000);

    setReasonTimeout(timeout);
  };

  // Handle reason selection
  const handleReasonClick = (reason: string) => {
    if (selectedRating && reasonTimeout && !isSubmitted) {
      clearTimeout(reasonTimeout);
      submitFeedback(selectedRating, reason);
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

  // Helper function to get button class based on state
  const getButtonClass = (rating: number) => {
    if (isSubmitted) {
      return selectedRating && selectedRating >= rating
        ? "text-yellow-400 cursor-not-allowed"
        : "text-gray-300 opacity-50 cursor-not-allowed";
    }

    return selectedRating && selectedRating >= rating
      ? "text-yellow-400"
      : "text-gray-300 hover:text-yellow-200";
  };

  return (
    <div className="mt-3 flex flex-col gap-1">
      <div className="text-sm text-gray-500 mb-1">
        {isSubmitted
          ? i18n.t("FEEDBACK$THANK_YOU_FOR_FEEDBACK")
          : i18n.t("FEEDBACK$RATE_AGENT_PERFORMANCE")}
      </div>
      <div className="flex flex-col gap-1">
        <div className="flex gap-1 items-center">
          {[1, 2, 3, 4, 5].map((rating) => (
            <button
              type="button"
              key={rating}
              onClick={() => handleRatingClick(rating)}
              disabled={isSubmitted}
              className={cn("text-xl transition-all", getButtonClass(rating))}
              aria-label={`Rate ${rating} stars`}
            >
              ★
            </button>
          ))}
        </div>
        {/* Show selected reason below stars when submitted */}
        {isSubmitted && selectedReason && (
          <div className="text-sm text-gray-500">{selectedReason}</div>
        )}
      </div>

      {showReasons && !isSubmitted && (
        <div className="mt-1 flex flex-col gap-1">
          <div className="text-xs text-gray-500 mb-1">
            {i18n.t("FEEDBACK$SELECT_REASON")}
          </div>
          <div className="flex flex-col gap-0.5">
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
