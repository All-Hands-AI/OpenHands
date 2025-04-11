import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsSwitch } from "../settings-switch";

interface EnableAnalyticsSwitchProps {
  defaultIsToggled: boolean;
}

export function EnableAnalyticsSwitch({
  defaultIsToggled,
}: EnableAnalyticsSwitchProps) {
  const { t } = useTranslation();

  return (
    <SettingsSwitch
      testId="enable-analytics-switch"
      name="enable-analytics-switch"
      defaultIsToggled={defaultIsToggled}
    >
      {t(I18nKey.ANALYTICS$ENABLE)}
    </SettingsSwitch>
  );
}
