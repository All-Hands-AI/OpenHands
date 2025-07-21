import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings.svg?react";
import { TooltipButton } from "./tooltip-button";
import { I18nKey } from "#/i18n/declaration";
import { useConfig } from "#/hooks/query/use-config";

interface SettingsButtonProps {
  onClick?: () => void;
  disabled?: boolean;
}

export function SettingsButton({
  onClick,
  disabled = false,
}: SettingsButtonProps) {
  const { t } = useTranslation();
  const { data: config } = useConfig();

  // Determine the correct settings path based on app mode
  // In SaaS mode, navigate directly to user settings to avoid the LLM settings page
  const settingsPath =
    config?.APP_MODE === "saas" ? "/settings/user" : "/settings";

  return (
    <TooltipButton
      testId="settings-button"
      tooltip={t(I18nKey.SETTINGS$TITLE)}
      ariaLabel={t(I18nKey.SETTINGS$TITLE)}
      onClick={onClick}
      navLinkTo={settingsPath}
      disabled={disabled}
    >
      <SettingsIcon width={28} height={28} />
    </TooltipButton>
  );
}
