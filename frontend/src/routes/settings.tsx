import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";

function SettingsScreen() {
  const { data: config } = useConfig();
  const { data: settings } = useSettings();

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings?.GITHUB_TOKEN_IS_SET;

  return (
    <main>
      <h2>Account Settings</h2>
      {isSaas && <button type="button">Configure GitHub Repositories</button>}
      {!isSaas && <input data-testid="github-token-input" type="password" />}
      {isGitHubTokenSet && (
        <button type="button">Disconnect from GitHub</button>
      )}
      <input data-testid="language-input" type="text" />
      <input data-testid="enable-analytics-switch" type="text" />

      <h2>LLM Settings</h2>

      <button type="button">Reset to defaults</button>
      <button type="button">Save Changes</button>
    </main>
  );
}

export default SettingsScreen;
