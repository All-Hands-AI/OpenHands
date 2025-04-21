import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { I18nKey } from "#/i18n/declaration";

function AppSettingsScreen() {
  const { t } = useTranslation();
  const { mutate: saveSettings } = useSaveSettings();
  const { data: settings } = useSettings();

  const [languageInputHasChanged, setLanguageInputHasChanged] =
    React.useState(false);
  const [analyticsSwitchHasChanged, setAnalyticsSwitchHasChanged] =
    React.useState(false);
  const [
    soundNotificationsSwitchHasChanged,
    setSoundNotificationsSwitchHasChanged,
  ] = React.useState(false);

  const formAction = (formData: FormData) => {
    const languageLabel = formData.get("language-input")?.toString();
    const languageValue = AvailableLanguages.find(
      ({ label }) => label === languageLabel,
    )?.value;
    const language = languageValue || DEFAULT_SETTINGS.LANGUAGE;

    const enableAnalytics =
      formData.get("enable-analytics-switch")?.toString() === "on";
    const enableSoundNotifications =
      formData.get("enable-sound-notifications-switch")?.toString() === "on";

    saveSettings({
      LANGUAGE: language,
      user_consents_to_analytics: enableAnalytics,
      ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
    });
  };

  const checkIfLanguageInputHasChanged = (value: string) => {
    const selectedLanguage = AvailableLanguages.find(
      ({ label: langValue }) => langValue === value,
    )?.label;
    const currentLanguage = AvailableLanguages.find(
      ({ value: langValue }) => langValue === settings?.LANGUAGE,
    )?.label;

    setLanguageInputHasChanged(selectedLanguage !== currentLanguage);
  };

  const checkIfAnalyticsSwitchHasChanged = (checked: boolean) => {
    const currentAnalytics = !!settings?.USER_CONSENTS_TO_ANALYTICS;
    setAnalyticsSwitchHasChanged(checked !== currentAnalytics);
  };

  const checkIfSoundNotificationsSwitchHasChanged = (checked: boolean) => {
    const currentSoundNotifications = !!settings?.ENABLE_SOUND_NOTIFICATIONS;
    setSoundNotificationsSwitchHasChanged(
      checked !== currentSoundNotifications,
    );
  };

  const submitButtonIsDisabled =
    !languageInputHasChanged &&
    !analyticsSwitchHasChanged &&
    !soundNotificationsSwitchHasChanged;

  return (
    <form data-testid="app-settings-screen" action={formAction}>
      {settings && (
        <SettingsDropdownInput
          testId="language-input"
          onChange={checkIfLanguageInputHasChanged}
          label={t(I18nKey.SETTINGS$LANGUAGE)}
          items={AvailableLanguages.map((l) => ({
            key: l.value,
            label: l.label,
          }))}
          defaultSelectedKey={settings?.LANGUAGE}
          name="language-input"
          isClearable={false}
        />
      )}

      {settings && (
        <SettingsSwitch
          testId="enable-analytics-switch"
          name="enable-analytics-switch"
          defaultIsToggled={!!settings.USER_CONSENTS_TO_ANALYTICS}
          onToggle={checkIfAnalyticsSwitchHasChanged}
        >
          {t(I18nKey.ANALYTICS$ENABLE)}
        </SettingsSwitch>
      )}

      {settings && (
        <SettingsSwitch
          testId="enable-sound-notifications-switch"
          name="enable-sound-notifications-switch"
          defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
          onToggle={checkIfSoundNotificationsSwitchHasChanged}
        >
          {t(I18nKey.SETTINGS$SOUND_NOTIFICATIONS)}
        </SettingsSwitch>
      )}

      <BrandButton
        testId="submit-button"
        variant="primary"
        type="submit"
        isDisabled={submitButtonIsDisabled}
      >
        Save Changes
      </BrandButton>
    </form>
  );
}

export default AppSettingsScreen;
