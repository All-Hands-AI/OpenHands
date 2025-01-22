import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";
import ExportIcon from "#/icons/export.svg?react";
import { FeedbackActionButton } from "#/components/shared/buttons/feedback-action-button";
import { ExportActionButton } from "#/components/shared/buttons/export-action-button";

interface TrajectoryActionsProps {
  onPositiveFeedback: () => void;
  onNegativeFeedback: () => void;
  onExportTrajectory: () => void;
}

export function TrajectoryActions({
  onPositiveFeedback,
  onNegativeFeedback,
  onExportTrajectory,
}: TrajectoryActionsProps) {
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
      <ExportActionButton
        testId="export-trajectory"
        onClick={onExportTrajectory}
        icon={<ExportIcon width={15} height={15} />}
      />
    </div>
  );
}
