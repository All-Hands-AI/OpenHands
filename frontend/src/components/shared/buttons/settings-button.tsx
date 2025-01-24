import { FaCog } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { TooltipButton } from "./tooltip-button";
import { I18nKey } from "#/i18n/declaration";

interface SettingsButtonProps {
  onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
  const { t } = useTranslation();
  return (
    <TooltipButton
      testId="settings-button"
      tooltip={t(I18nKey.SETTINGS$TITLE)}
      ariaLabel={t(I18nKey.SETTINGS$TITLE)}
      onClick={onClick}
    >
      <FaCog size={24} />
    </TooltipButton>
  );
}
