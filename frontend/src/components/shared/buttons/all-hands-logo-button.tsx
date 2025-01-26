import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { TooltipButton } from "./tooltip-button";

interface AllHandsLogoButtonProps {
  onClick: () => void;
}

export function AllHandsLogoButton({ onClick }: AllHandsLogoButtonProps) {
  return (
    <TooltipButton
      tooltip="All Hands AI"
      ariaLabel="All Hands Logo"
      onClick={onClick}
    >
      <AllHandsLogo width={44} height={30} />
    </TooltipButton>
  );
}
