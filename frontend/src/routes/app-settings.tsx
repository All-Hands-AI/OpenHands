import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";

function AppSettingsScreen() {
  const { data: settings } = useSettings();
  const language = AvailableLanguages.find(
    (lang) => lang.value === settings?.LANGUAGE,
  )?.label;

  return (
    <div data-testid="app-settings-screen">
      <input data-testid="language-input" defaultValue={language} />

      {settings && (
        <input
          type="checkbox"
          data-testid="enable-analytics-switch"
          defaultChecked={!!settings.USER_CONSENTS_TO_ANALYTICS}
        />
      )}

      {settings && (
        <input
          type="checkbox"
          data-testid="enable-sound-notifications-switch"
          defaultChecked={!!settings.ENABLE_SOUND_NOTIFICATIONS}
        />
      )}
    </div>
  );
}

export default AppSettingsScreen;
