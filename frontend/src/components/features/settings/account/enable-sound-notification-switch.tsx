import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsSwitch } from "../settings-switch";

export function EnableSoundNotificationsSwitch({
  defaultIsToggled,
}: {
  defaultIsToggled: boolean;
}) {
  const { t } = useTranslation();

  return (
    <SettingsSwitch
      testId="enable-sound-notifications-switch"
      name="enable-sound-notifications-switch"
      defaultIsToggled={defaultIsToggled}
    >
      {t(I18nKey.SETTINGS$SOUND_NOTIFICATIONS)}
    </SettingsSwitch>
  );
}
