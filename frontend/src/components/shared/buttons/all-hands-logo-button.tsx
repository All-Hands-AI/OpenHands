import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { TooltipButton } from "./tooltip-button";

interface AllHandsLogoButtonProps {
  onClick: () => void;
}

export function AllHandsLogoButton({ onClick }: AllHandsLogoButtonProps) {
  return (
    <TooltipButton tooltip="Thesis" ariaLabel="Thesis Logo" onClick={onClick}>
      <AllHandsLogo />
    </TooltipButton>
  );
}
