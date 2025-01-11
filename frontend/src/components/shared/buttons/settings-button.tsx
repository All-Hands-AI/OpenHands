import { FaCog } from "react-icons/fa";
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
      <FaCog size={24} />
    </TooltipButton>
  );
}
