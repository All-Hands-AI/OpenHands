import CogTooth from "#/assets/cog-tooth";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";

interface SettingsButtonProps {
  onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
  const { t } = useTranslation();
  return (
    <TooltipButton
      testId="settings-button"
      tooltip={t(I18nKey.SIDEBAR$SETTINGS)}
      ariaLabel={t(I18nKey.SIDEBAR$SETTINGS)}
      onClick={onClick}
    >
      <CogTooth />
    </TooltipButton>
  );
}
