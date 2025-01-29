import { useTranslation } from "react-i18next";
import { Switch } from "@nextui-org/react";
import { I18nKey } from "#/i18n/declaration";

interface SoundNotificationsSwitchProps {
  isDisabled?: boolean;
  defaultSelected?: boolean;
}

export function SoundNotificationsSwitch({
  isDisabled,
  defaultSelected,
}: SoundNotificationsSwitchProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-1">
      <Switch
        name="ENABLE_SOUND_NOTIFICATIONS"
        isDisabled={isDisabled}
        defaultSelected={defaultSelected}
        size="sm"
      >
        {t(I18nKey.SETTINGS$ENABLE_SOUND_NOTIFICATIONS)}
      </Switch>
      <span className="text-xs text-gray-400">
        {t(I18nKey.SETTINGS$ENABLE_SOUND_NOTIFICATIONS_DESCRIPTION)}
      </span>
    </div>
  );
}