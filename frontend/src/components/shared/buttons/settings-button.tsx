import CogTooth from "#/assets/cog-tooth";
import { TooltipButton } from "./tooltip-button";

interface SettingsButtonProps {
  onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
  return (
    <TooltipButton
      testId="settings-button"
      tooltip="Settings"
      ariaLabel="Settings"
      onClick={onClick}
    >
      <CogTooth />
    </TooltipButton>
  );
}
