import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsSwitch } from "../settings-switch";

interface EnableConfirmationModeSwitchProps {
  onToggle: (isEnabled: boolean) => void;
  defaultIsToggled: boolean;
}

export function EnableConfirmationModeSwitch({
  defaultIsToggled,
  onToggle,
}: EnableConfirmationModeSwitchProps) {
  const { t } = useTranslation();

  return (
    <SettingsSwitch
      testId="enable-confirmation-mode-switch"
      onToggle={onToggle}
      defaultIsToggled={defaultIsToggled}
      isBeta
    >
      {t(I18nKey.SETTINGS$CONFIRMATION_MODE)}
    </SettingsSwitch>
  );
}
