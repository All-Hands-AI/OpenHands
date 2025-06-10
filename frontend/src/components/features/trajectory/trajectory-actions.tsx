import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import ExportIcon from "#/icons/export.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";

interface TrajectoryActionsProps {
  onExportTrajectory: () => void;
}

export function TrajectoryActions({
  onExportTrajectory,
}: TrajectoryActionsProps) {
  const { t } = useTranslation();

  return (
    <div data-testid="trajectory-actions" className="flex gap-1">
      <TrajectoryActionButton
        testId="export-trajectory"
        onClick={onExportTrajectory}
        icon={<ExportIcon width={15} height={15} />}
        tooltip={t(I18nKey.BUTTON$EXPORT_CONVERSATION)}
      />
    </div>
  );
}
