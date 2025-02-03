import React from "react";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { HelpLink } from "#/components/features/settings/help-link";
import { SettingsDropdown } from "#/components/features/settings/settings-dropdown";
import { AvailableLanguages } from "#/i18n";
import { Settings } from "#/types/settings";
import { DEFAULT_SETTINGS } from "#/services/settings";

const hasAdvancedSettingsSet = (settings: Settings) =>
  settings.CONFIRMATION_MODE ||
  settings.LLM_BASE_URL ||
  settings.AGENT !== DEFAULT_SETTINGS.AGENT ||
  settings.REMOTE_RUNTIME_RESOURCE_FACTOR !==
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR ||
  settings.SECURITY_ANALYZER;

function SettingsScreen() {
  const { data: config } = useConfig();
  const { data: settings } = useSettings();

  const [llmConfigMode, setLlmConfigMode] = React.useState<
    "basic" | "advanced"
  >("basic");
  const [confirmationModeIsEnabled, setConfirmationModeIsEnabled] =
    React.useState(false);

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings?.GITHUB_TOKEN_IS_SET;
  const isAnalyticsEnabled = settings?.USER_CONSENTS_TO_ANALYTICS;

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
            defaultValue={settings?.LANGUAGE}
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
              placeholder="openai/gpt-4o"
              type="text"
              className="w-[680px]"
            />
          )}
          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="base-url-input"
              label="Base URL"
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
