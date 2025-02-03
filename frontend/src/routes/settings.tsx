import React from "react";
import { useLoaderData } from "react-router";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { HelpLink } from "#/components/features/settings/help-link";
import { SettingsDropdown } from "#/components/features/settings/settings-dropdown";
import { AvailableLanguages } from "#/i18n";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import OpenHands from "#/api/open-hands";

export const clientLoader = async () => {
  const settings = await OpenHands.getSettings();
  const config = await OpenHands.getConfig();

  return { settings, config };
};

function SettingsScreen() {
  const { settings, config } = useLoaderData<typeof clientLoader>();

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings.github_token_is_set;
  const isAnalyticsEnabled = settings.user_consents_to_analytics;
  const isAdvancedSettingsSet = hasAdvancedSettingsSet(settings);

  const [llmConfigMode, setLlmConfigMode] = React.useState<
    "basic" | "advanced"
  >(isAdvancedSettingsSet ? "advanced" : "basic");
  const [confirmationModeIsEnabled, setConfirmationModeIsEnabled] =
    React.useState(!!settings.security_analyzer);

  return (
    <main className="bg-[#24272E] border border-[#454545] h-full rounded-xl">
      <form action="" className="flex flex-col h-full">
        <header className="text-sm leading-6 px-3 py-1.5 border-b border-b-[#454545]">
          Settings
        </header>

        <div className="flex flex-col gap-6 grow overflow-y-auto px-11 py-9">
          <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
            Account Settings
          </h2>
          {isSaas && (
            <BrandButton variant="secondary">
              Configure GitHub Repositories
            </BrandButton>
          )}
          {!isSaas && (
            <>
              <SettingsInput
                testId="github-token-input"
                label="GitHub Token"
                type="password"
                className="w-[680px]"
              />

              <HelpLink
                testId="github-token-help-anchor"
                text="Get your token"
                linkText="here"
                href="https://docs.all-hands.dev/modules/usage/llms"
              />
            </>
          )}

          {isGitHubTokenSet && (
            <BrandButton variant="secondary">
              Disconnect from GitHub
            </BrandButton>
          )}

          <SettingsDropdown
            testId="language-input"
            label="Language"
            options={AvailableLanguages}
            defaultValue={settings.language}
            showOptionalTag
            className="w-[680px]"
          />

          <SettingsSwitch
            testId="enable-analytics-switch"
            showOptionalTag
            defaultIsToggled={!!isAnalyticsEnabled}
          >
            Enable analytics
          </SettingsSwitch>

          <div className="flex items-center gap-7">
            <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
              LLM Settings
            </h2>
            <SettingsSwitch
              testId="advanced-settings-switch"
              defaultIsToggled={isAdvancedSettingsSet}
              onToggle={(isToggled) =>
                setLlmConfigMode(isToggled ? "advanced" : "basic")
              }
            >
              Advanced
            </SettingsSwitch>
          </div>

          {llmConfigMode === "basic" && (
            <div className="flex w-[680px] justify-between gap-[46px]">
              <SettingsInput
                testId="llm-provider-input"
                label="LLM Provider"
                type="text"
                className="flex grow"
              />
              <SettingsInput
                testId="llm-model-input"
                label="LLM Model"
                type="text"
                className="flex grow"
              />
            </div>
          )}

          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="llm-custom-model-input"
              label="Custom Model"
              defaultValue={settings.llm_model}
              placeholder="anthropic/claude-3-5-sonnet-20241022"
              type="text"
              className="w-[680px]"
            />
          )}
          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="base-url-input"
              label="Base URL"
              defaultValue={settings.llm_base_url}
              placeholder="https://api.openai.com"
              type="text"
              className="w-[680px]"
            />
          )}

          <SettingsInput
            testId="llm-api-key-input"
            label="API Key"
            type="password"
            className="w-[680px]"
          />

          <HelpLink
            testId="llm-api-key-help-anchor"
            text="Don't know your API key?"
            linkText="Click here for instructions"
            href="https://docs.all-hands.dev/modules/usage/llms"
          />

          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="agent-input"
              label="Agent"
              defaultValue={settings.agent}
              type="text"
              className="w-[680px]"
            />
          )}

          {isSaas && llmConfigMode === "advanced" && (
            <SettingsInput
              testId="runtime-settings-input"
              label="Runtime Settings"
              type="text"
              className="w-[680px]"
            />
          )}

          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="security-analyzer-input"
              label="Security Analyzer"
              defaultValue={settings.security_analyzer}
              type="text"
              className="w-[680px]"
              isDisabled={!confirmationModeIsEnabled}
              showOptionalTag
            />
          )}
          {llmConfigMode === "advanced" && (
            <SettingsSwitch
              testId="enable-confirmation-mode-switch"
              onToggle={setConfirmationModeIsEnabled}
              defaultIsToggled={!!settings.security_analyzer}
              showOptionalTag
            >
              Enable confirmation mode
            </SettingsSwitch>
          )}
        </div>

        <footer className="flex gap-6 p-6 justify-end border-t border-t-[#454545]">
          <BrandButton variant="secondary">Reset to defaults</BrandButton>
          <BrandButton variant="primary">Save Changes</BrandButton>
        </footer>
      </form>
    </main>
  );
}

export default SettingsScreen;
