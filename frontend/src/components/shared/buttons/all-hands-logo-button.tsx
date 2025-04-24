import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { Tooltip } from "@heroui/react";
import { cn } from "#/utils/utils";

interface AllHandsLogoButtonProps {
  onClick: () => void;
}

export function AllHandsLogoButton({ onClick }: AllHandsLogoButtonProps) {
  const { t } = useTranslation();

  // Handle click with support for cmd/ctrl+click to open in new tab
  const handleClick = (e: React.MouseEvent) => {
    // If cmd/ctrl key is pressed, let the default behavior happen (open in new tab)
    if (e.metaKey || e.ctrlKey) {
      return; // Don't prevent default to allow browser to handle opening in new tab
    }

    // Otherwise, call the onClick handler
    onClick();
    e.preventDefault();
  };

  return (
    <Tooltip content={t(I18nKey.BRANDING$ALL_HANDS_AI)} closeDelay={100} placement="right">
      <NavLink
        to="/"
        onClick={handleClick}
        className={cn("hover:opacity-80")}
        aria-label={t(I18nKey.BRANDING$ALL_HANDS_LOGO)}
      >
        <AllHandsLogo width={34} height={34} />
      </NavLink>
    </Tooltip>
  );
}
