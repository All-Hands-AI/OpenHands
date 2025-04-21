import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";

function AppSettingsScreen() {
  const { mutate: saveSettings } = useSaveSettings();
  const { data: settings } = useSettings();

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

  return (
    <form data-testid="app-settings-screen" action={formAction}>
      {settings && (
        <SettingsDropdownInput
          testId="language-input"
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
        />
      )}

      {settings && (
        <input
          type="checkbox"
          data-testid="enable-sound-notifications-switch"
          name="enable-sound-notifications-switch"
          defaultChecked={!!settings.ENABLE_SOUND_NOTIFICATIONS}
        />
      )}

      <button data-testid="submit-button" type="submit">
        Submit
      </button>
    </form>
  );
}

export default AppSettingsScreen;
