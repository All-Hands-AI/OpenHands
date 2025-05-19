import { useTranslation } from "react-i18next";
import { useState } from "react";
import { I18nKey } from "#/i18n/declaration";
import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";
import ExportIcon from "#/icons/export.svg?react";
import CodeIcon from "#/icons/code.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";
import { MicroagentDropdown } from "./microagent-dropdown";

interface TrajectoryActionsProps {
  onPositiveFeedback: () => void;
  onNegativeFeedback: () => void;
  onExportTrajectory: () => void;
  onInsertMicroagent?: (content: string) => void;
}

export function TrajectoryActions({
  onPositiveFeedback,
  onNegativeFeedback,
  onExportTrajectory,
  onInsertMicroagent,
}: TrajectoryActionsProps) {
  const { t } = useTranslation();
  const [isMicroagentDropdownOpen, setIsMicroagentDropdownOpen] =
    useState(false);

  const handleMicroagentButtonClick = () => {
    setIsMicroagentDropdownOpen(!isMicroagentDropdownOpen);
  };

  const handleMicroagentSelect = (content: string) => {
    if (onInsertMicroagent) {
      onInsertMicroagent(content);
    }
    setIsMicroagentDropdownOpen(false);
  };

  const handleDropdownClose = () => {
    setIsMicroagentDropdownOpen(false);
  };

  return (
    <div data-testid="feedback-actions" className="flex gap-1 relative">
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
      <TrajectoryActionButton
        testId="export-trajectory"
        onClick={onExportTrajectory}
        icon={<ExportIcon width={15} height={15} />}
        tooltip={t(I18nKey.BUTTON$EXPORT_CONVERSATION)}
      />
      {onInsertMicroagent && (
        <TrajectoryActionButton
          testId="microagent-button"
          onClick={handleMicroagentButtonClick}
          icon={<CodeIcon width={15} height={15} />}
          tooltip={t(I18nKey.BUTTON$SHOW_MICROAGENTS)}
        />
      )}

      {isMicroagentDropdownOpen && onInsertMicroagent && (
        <MicroagentDropdown
          isOpen={isMicroagentDropdownOpen}
          onClose={handleDropdownClose}
          onSelectMicroagent={handleMicroagentSelect}
        />
      )}
    </div>
  );
}
