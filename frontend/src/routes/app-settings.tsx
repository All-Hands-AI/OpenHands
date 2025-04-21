import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";

function AppSettingsScreen() {
  const { data: settings } = useSettings();

  return (
    <div data-testid="app-settings-screen">
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
