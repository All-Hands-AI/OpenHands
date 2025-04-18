import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";

function GitSettingsScreen() {
  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  return (
    <div data-testid="git-settings-screen">
      {config?.APP_MODE === "saas" && config.APP_SLUG && (
        <div data-testid="configure-github-repositories-button" />
      )}
      {config?.APP_MODE === "oss" && (
        <input
          data-testid="github-token-input"
          placeholder={settings?.PROVIDER_TOKENS_SET.github ? "<hidden>" : ""}
        />
      )}
      {config?.APP_MODE === "oss" && (
        <div data-testid="github-token-help-anchor" />
      )}
    </div>
  );
}

export default GitSettingsScreen;
