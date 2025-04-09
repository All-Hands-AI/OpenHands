import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsSwitch } from "../settings-switch";

interface EnableMemoryCondensorSwitchProps {
  defaultIsToggled: boolean;
}

export function EnableMemoryCondensorSwitch({
  defaultIsToggled,
}: EnableMemoryCondensorSwitchProps) {
  const { t } = useTranslation();

  return (
    <SettingsSwitch
      testId="enable-memory-condenser-switch"
      name="enable-memory-condenser-switch"
      defaultIsToggled={defaultIsToggled}
    >
      {t(I18nKey.SETTINGS$ENABLE_MEMORY_CONDENSATION)}
    </SettingsSwitch>
  );
}
