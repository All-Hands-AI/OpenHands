import React from "react";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";

function AppSettingsScreen() {
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

  return (
    <form data-testid="app-settings-screen" action={formAction}>
      {settings && (
        <SettingsDropdownInput
          testId="language-input"
          onChange={checkIfLanguageInputHasChanged}
          items={AvailableLanguages.map((l) => ({
            key: l.value,
            label: l.label,
          }))}
          defaultSelectedKey={settings?.LANGUAGE}
          name="language-input"
          label="Language"
          isClearable={false}
        />
      )}

      {settings && (
        <input
          type="checkbox"
          data-testid="enable-analytics-switch"
          name="enable-analytics-switch"
          defaultChecked={!!settings.USER_CONSENTS_TO_ANALYTICS}
          onChange={(e) => checkIfAnalyticsSwitchHasChanged(e.target.checked)}
        />
      )}

      {settings && (
        <input
          type="checkbox"
          data-testid="enable-sound-notifications-switch"
          name="enable-sound-notifications-switch"
          defaultChecked={!!settings.ENABLE_SOUND_NOTIFICATIONS}
          onChange={(e) =>
            checkIfSoundNotificationsSwitchHasChanged(e.target.checked)
          }
        />
      )}

      <button
        data-testid="submit-button"
        type="submit"
        disabled={
          !languageInputHasChanged &&
          !analyticsSwitchHasChanged &&
          !soundNotificationsSwitchHasChanged
        }
      >
        Save Changes
      </button>
    </form>
  );
}

export default AppSettingsScreen;
