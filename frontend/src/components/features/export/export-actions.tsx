import ExportIcon from "#/icons/export.svg?react";
import { ExportActionButton } from "#/components/shared/buttons/export-action-button";

interface ExportActionsProps {
  onExportTrajectory: () => void;
}

export function ExportActions({ onExportTrajectory }: ExportActionsProps) {
  return (
    <div data-testid="export-actions" className="flex gap-1">
      <ExportActionButton
        onClick={onExportTrajectory}
        icon={<ExportIcon width={15} height={15} />}
      />
    </div>
  );
}
