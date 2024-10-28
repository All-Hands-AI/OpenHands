import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";

interface FeedbackActionButtonProps {
  testId?: string;
  onClick: () => void;
  icon: React.ReactNode;
}

function FeedbackActionButton({
  testId,
  onClick,
  icon,
}: FeedbackActionButtonProps) {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      className="p-1 bg-neutral-700 border border-neutral-600 rounded hover:bg-neutral-500"
    >
      {icon}
    </button>
  );
}

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
