import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";

function GitSettingsScreen() {
  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";

  return (
    <div data-testid="git-settings-screen">
      {isSaas && config.APP_SLUG && (
        <div data-testid="configure-github-repositories-button" />
      )}

      {!isSaas && (
        <>
          <input
            data-testid="github-token-input"
            placeholder={settings?.PROVIDER_TOKENS_SET.github ? "<hidden>" : ""}
          />
          <div data-testid="github-token-help-anchor" />
        </>
      )}
    </div>
  );
}

export default GitSettingsScreen;
