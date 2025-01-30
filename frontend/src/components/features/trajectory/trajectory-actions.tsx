import { HiVolumeUp, HiVolumeOff } from "react-icons/hi";
import ThumbsUpIcon from "#/icons/thumbs-up.svg?react";
import ThumbDownIcon from "#/icons/thumbs-down.svg?react";
import ExportIcon from "#/icons/export.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";
import { useCurrentSettings } from "#/context/settings-context";

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
  const { settings, saveUserSettings } = useCurrentSettings();

  const toggleSound = async () => {
    await saveUserSettings({
      ...settings,
      ENABLE_SOUND_NOTIFICATIONS: !settings?.ENABLE_SOUND_NOTIFICATIONS,
    });
  };
  return (
    <div data-testid="feedback-actions" className="flex gap-1">
      <TrajectoryActionButton
        testId="positive-feedback"
        onClick={onPositiveFeedback}
        icon={<ThumbsUpIcon width={15} height={15} />}
      />
      <TrajectoryActionButton
        testId="negative-feedback"
        onClick={onNegativeFeedback}
        icon={<ThumbDownIcon width={15} height={15} />}
      />
      <TrajectoryActionButton
        testId="export-trajectory"
        onClick={onExportTrajectory}
        icon={<ExportIcon width={15} height={15} />}
      />
      <TrajectoryActionButton
        testId="sound-toggle"
        onClick={toggleSound}
        icon={
          settings?.ENABLE_SOUND_NOTIFICATIONS !== false ? (
            <HiVolumeUp size={15} />
          ) : (
            <HiVolumeOff size={15} />
          )
        }
      />
    </div>
  );
}
