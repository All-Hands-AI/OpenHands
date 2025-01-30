import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";

function SettingsScreen() {
  const { data: config } = useConfig();
  const { data: settings } = useSettings();

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings?.GITHUB_TOKEN_IS_SET;

  return (
    <main className="bg-[#24272E] border border-[#454545] h-full rounded-xl">
      <form action="" className="flex flex-col h-full">
        <div className="flex flex-col gap-6 grow">
          <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
            Account Settings
          </h2>

          {isSaas && (
            <button type="button">Configure GitHub Repositories</button>
          )}
          {!isSaas && (
            <SettingsInput
              testId="github-token-input"
              label="GitHub Token"
              type="password"
            />
          )}

          {isGitHubTokenSet && (
            <BrandButton variant="primary">Disconnect from GitHub</BrandButton>
          )}
          <label className="flex flex-col gap-2">
            <span className="text-sm">Language</span>
            <input
              data-testid="language-input"
              type="text"
              className="bg-[#454545] border border-[#717888] h-10 w-[680px] rounded p-2"
            />
          </label>

          <SettingsSwitch testId="enable-analytics-switch" showOptionalTag>
            Enable analytics
          </SettingsSwitch>

          <h2>LLM Settings</h2>
        </div>

        <footer className="flex gap-6 p-6 justify-end border-t border-t-[#717888]">
          <BrandButton variant="secondary">Reset to defaults</BrandButton>
          <BrandButton variant="primary">Save Changes</BrandButton>
        </footer>
      </form>
    </main>
  );
}

export default SettingsScreen;
