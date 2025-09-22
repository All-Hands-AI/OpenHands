import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";

interface TrajectoryActionsProps {
  onPositiveFeedback: () => void;
  onNegativeFeedback: () => void;
  isSaasMode?: boolean;
}

export function TrajectoryActions({
  onPositiveFeedback,
  onNegativeFeedback,
  isSaasMode = false,
}: TrajectoryActionsProps) {
  const { t } = useTranslation();

  return (
    <div data-testid="feedback-actions" className="flex gap-1">
      {!isSaasMode && (
        <>
          <TrajectoryActionButton
            testId="positive-feedback"
            onClick={onPositiveFeedback}
            icon={<ThumbsUpIcon width={15} height={15} />}
            tooltip={t(I18nKey.BUTTON$MARK_HELPFUL)}
          />
          <TrajectoryActionButton
            testId="negative-feedback"
            onClick={onNegativeFeedback}
            icon={<ThumbDownIcon width={15} height={15} />}
            tooltip={t(I18nKey.BUTTON$MARK_NOT_HELPFUL)}
          />
        </>
      )}
    </div>
  );
}
