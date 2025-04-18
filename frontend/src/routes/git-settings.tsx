import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";

function GitSettingsScreen() {
  const { mutate: saveSettings } = useSaveSettings();
  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";

  const formAction = async (formData: FormData) => {
    const githubToken = formData.get("github-token-input")?.toString() || "";
    const gitlabToken = formData.get("gitlab-token-input")?.toString() || "";

    saveSettings({
      provider_tokens: {
        github: githubToken,
        gitlab: gitlabToken,
      },
    });
  };

  return (
    <form data-testid="git-settings-screen" action={formAction}>
      {isSaas && config.APP_SLUG && (
        <div data-testid="configure-github-repositories-button" />
      )}

      {!isSaas && (
        <>
          <input
            data-testid="github-token-input"
            name="github-token-input"
            placeholder={settings?.PROVIDER_TOKENS_SET.github ? "<hidden>" : ""}
          />
          <div data-testid="github-token-help-anchor" />
        </>
      )}

      {!isSaas && (
        <>
          <input
            data-testid="gitlab-token-input"
            name="gitlab-token-input"
            placeholder={settings?.PROVIDER_TOKENS_SET.gitlab ? "<hidden>" : ""}
          />
          <div data-testid="gitlab-token-help-anchor" />
        </>
      )}

      <button data-testid="submit-button" type="submit">
        Submit
      </button>
    </form>
  );
}

export default GitSettingsScreen;
