import { useTranslation } from "react-i18next";
import { Button } from "@nextui-org/react";
import { HiVolumeUp, HiVolumeOff } from "react-icons/hi";
import { useCurrentSettings } from "#/context/settings-context";
import { I18nKey } from "#/i18n/declaration";

export function SoundToggleButton() {
  const { t } = useTranslation();
  const { settings, saveUserSettings } = useCurrentSettings();

  const toggleSound = async () => {
    await saveUserSettings({
      ...settings,
      ENABLE_SOUND_NOTIFICATIONS: !settings?.ENABLE_SOUND_NOTIFICATIONS,
    });
  };

  return (
    <Button
      isIconOnly
      variant="light"
      aria-label={t(
        settings?.ENABLE_SOUND_NOTIFICATIONS
          ? I18nKey.BUTTON$DISABLE_SOUND
          : I18nKey.BUTTON$ENABLE_SOUND,
      )}
      onClick={toggleSound}
    >
      {settings?.ENABLE_SOUND_NOTIFICATIONS ? (
        <HiVolumeUp className="text-default-500" />
      ) : (
        <HiVolumeOff className="text-default-500" />
      )}
    </Button>
  );
}
