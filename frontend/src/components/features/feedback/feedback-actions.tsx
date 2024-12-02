import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";
import { FeedbackActionButton } from "#/components/shared/buttons/feedback-action-button";

interface FeedbackActionsProps {
  onPositiveFeedback: () => void;
  onNegativeFeedback: () => void;
}

export function FeedbackActions({
  onPositiveFeedback,
  onNegativeFeedback,
}: FeedbackActionsProps) {
  return (
    <div data-testid="feedback-actions" className="flex gap-1">
      <FeedbackActionButton
        testId="positive-feedback"
        onClick={onPositiveFeedback}
        icon={<ThumbsUpIcon width={15} height={15} />}
      />
      <FeedbackActionButton
        testId="negative-feedback"
        onClick={onNegativeFeedback}
        icon={<ThumbDownIcon width={15} height={15} />}
      />
    </div>
  );
}
