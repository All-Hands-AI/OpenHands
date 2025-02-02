import { HiVolumeUp, HiVolumeOff } from "react-icons/hi";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
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
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { settings, saveUserSettings } = useCurrentSettings();
  const soundEnabled = settings?.ENABLE_SOUND_NOTIFICATIONS ?? true;

  const toggleSound = async () => {
    try {
      const newSettings = {
        ...settings,
        ENABLE_SOUND_NOTIFICATIONS: !soundEnabled,
      };
      await saveUserSettings(newSettings);
      // Wait for the settings to be saved before invalidating
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      // Immediately update the local state to avoid flicker
      queryClient.setQueryData(["settings"], newSettings);
    } catch (error) {
      toast.error(t("Failed to save sound settings. Please try again."));
    }
  };
  return (
    <div data-testid="feedback-actions" className="flex gap-1">
      <TrajectoryActionButton
        testId="positive-feedback"
        onClick={onPositiveFeedback}
        icon={<ThumbsUpIcon width={15} height={15} />}
        tooltip={t("BUTTON$MARK_HELPFUL")}
      />
      <TrajectoryActionButton
        testId="negative-feedback"
        onClick={onNegativeFeedback}
        icon={<ThumbDownIcon width={15} height={15} />}
        tooltip={t("BUTTON$MARK_NOT_HELPFUL")}
      />
      <TrajectoryActionButton
        testId="export-trajectory"
        onClick={onExportTrajectory}
        icon={<ExportIcon width={15} height={15} />}
        tooltip={t("BUTTON$EXPORT_CONVERSATION")}
      />
      <TrajectoryActionButton
        testId="sound-toggle"
        onClick={toggleSound}
        icon={
          soundEnabled ? <HiVolumeUp size={15} /> : <HiVolumeOff size={15} />
        }
        tooltip={t(
          soundEnabled ? "BUTTON$DISABLE_SOUND" : "BUTTON$ENABLE_SOUND",
        )}
      />
    </div>
  );
}
