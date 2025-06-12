import React, { useState, useEffect, useContext } from "react";
import { cn } from "#/utils/utils";
import i18n from "#/i18n";
import { useSubmitConversationFeedback } from "#/hooks/mutation/use-submit-conversation-feedback";
import { ScrollContext } from "#/context/scroll-context";

// Global timeout duration in milliseconds
const AUTO_SUBMIT_TIMEOUT = 10000;

interface LikertScaleProps {
  eventId?: number;
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
  eventId,
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
  const [countdown, setCountdown] = useState<number>(0);

  // Get scroll context
  const scrollContext = useContext(ScrollContext);

  // If scrollContext is undefined, we're not inside a ScrollProvider
  const scrollToBottom = scrollContext?.scrollDomToBottom;

  // Use our mutation hook
  const { mutate: submitConversationFeedback } =
    useSubmitConversationFeedback();

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
    submitConversationFeedback(
      {
        rating,
        eventId,
        reason,
      },
      {
        onSuccess: () => {
          setSelectedReason(reason || null);
          setShowReasons(false);
          setIsSubmitted(true);
        },
      },
    );
  };

  // Handle star rating selection
  const handleRatingClick = (rating: number) => {
    if (isSubmitted) return; // Prevent changes after submission

    setSelectedRating(rating);

    // Only show reasons if rating is 3 or less (1, 2, or 3 stars)
    // For ratings > 3 (4 or 5 stars), submit immediately without showing reasons
    if (rating <= 3) {
      setShowReasons(true);
      setCountdown(Math.ceil(AUTO_SUBMIT_TIMEOUT / 1000));

      // Set a timeout to auto-submit if no reason is selected
      const timeout = setTimeout(() => {
        submitFeedback(rating);
      }, AUTO_SUBMIT_TIMEOUT);

      setReasonTimeout(timeout);

      // Scroll to bottom to show the reasons
      if (scrollToBottom) {
        // Small delay to ensure the reasons are fully rendered
        setTimeout(() => {
          scrollToBottom();
        }, 100);
      }
    } else {
      // For ratings > 3 (4 or 5 stars), submit immediately without showing reasons
      setShowReasons(false);
      submitFeedback(rating);
    }
  };

  // Handle reason selection
  const handleReasonClick = (reason: string) => {
    if (selectedRating && reasonTimeout && !isSubmitted) {
      clearTimeout(reasonTimeout);
      setCountdown(0);
      submitFeedback(selectedRating, reason);
    }
  };

  // Countdown effect
  useEffect(() => {
    if (countdown > 0 && showReasons && !isSubmitted) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
    return () => {};
  }, [countdown, showReasons, isSubmitted]);

  // Clean up timeout on unmount
  useEffect(
    () => () => {
      if (reasonTimeout) {
        clearTimeout(reasonTimeout);
      }
    },
    [reasonTimeout],
  );

  // Scroll to bottom when component mounts
  useEffect(() => {
    if (scrollToBottom && !isSubmitted) {
      // Small delay to ensure the component is fully rendered
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  }, [scrollToBottom, isSubmitted]);

  // Scroll to bottom when reasons are shown
  useEffect(() => {
    if (scrollToBottom && showReasons) {
      // Small delay to ensure the reasons are fully rendered
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  }, [scrollToBottom, showReasons]);

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
        <span className="flex gap-2 items-center flex-wrap">
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
          {/* Show selected reason inline with stars when submitted (only for ratings <= 3) */}
          {isSubmitted &&
            selectedReason &&
            selectedRating &&
            selectedRating <= 3 && (
              <span className="text-sm text-gray-500 italic">
                {selectedReason}
              </span>
            )}
        </span>
      </div>

      {showReasons && !isSubmitted && (
        <div className="mt-1 flex flex-col gap-1">
          <div className="text-xs text-gray-500 mb-1">
            {i18n.t("FEEDBACK$SELECT_REASON")}
          </div>
          {countdown > 0 && (
            <div className="text-xs text-gray-400 mb-1 italic">
              {i18n.t("FEEDBACK$SELECT_REASON_COUNTDOWN", {
                countdown,
              })}
            </div>
          )}
          <div className="flex flex-col gap-0.5">
            {FEEDBACK_REASONS.map((reason) => (
              <button
                type="button"
                key={reason}
                onClick={() => handleReasonClick(reason)}
                className="text-sm text-left py-1 px-2 rounded hover:bg-gray-700 transition-colors"
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
