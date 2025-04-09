import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsSwitch } from "../settings-switch";

interface AdvancedSettingsSwitchProps {
  defaultIsToggled: boolean;
  onToggle: (isToggled: boolean) => void;
}

export function AdvancedSettingsSwitch({
  defaultIsToggled,
  onToggle,
}: AdvancedSettingsSwitchProps) {
  const { t } = useTranslation();

  return (
    <SettingsSwitch
      testId="advanced-settings-switch"
      defaultIsToggled={defaultIsToggled}
      onToggle={onToggle}
    >
      {t(I18nKey.SETTINGS$ADVANCED)}
    </SettingsSwitch>
  );
}
