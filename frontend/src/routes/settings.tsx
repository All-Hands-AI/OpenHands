import React from "react";
import { useFetcher, useLoaderData } from "react-router";
import toast from "react-hot-toast";
import { isAxiosError } from "axios";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { HelpLink } from "#/components/features/settings/help-link";
import { SettingsDropdown } from "#/components/features/settings/settings-dropdown";
import { AvailableLanguages } from "#/i18n";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import OpenHands from "#/api/open-hands";
import { Route } from "./+types/settings";
import { DEFAULT_SETTINGS } from "#/services/settings";

export const clientLoader = async () => {
  const settings = await OpenHands.getSettings();
  const config = await OpenHands.getConfig();

  return { settings, config };
};

export const clientAction = async ({ request }: Route.ClientActionArgs) => {
  const formData = await request.formData();

  const languageLabel = formData.get("language-input")?.toString();
  const languageValue = AvailableLanguages.find(
    ({ label }) => label === languageLabel,
  )?.value;

  const llmModel = formData.get("llm-custom-model-input")?.toString();

  const rawRemoteRuntimeResourceFactor =
    formData.get("runtime-settings-input")?.toString() ||
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR;
  const remoteRuntimeResourceFactor = Number(rawRemoteRuntimeResourceFactor);

  try {
    await OpenHands.saveSettings({
      github_token: formData.get("github-token-input")?.toString() || "",
      language: languageValue,
      user_consents_to_analytics:
        formData.get("enable-analytics-switch")?.toString() === "on",
      llm_model: llmModel,
      llm_base_url: formData.get("base-url-input")?.toString(),
      llm_api_key: formData.get("llm-api-key-input")?.toString() || null,
      agent: formData.get("agent-input")?.toString(),
      security_analyzer:
        formData.get("security-analyzer-input")?.toString() || "",
      remote_runtime_resource_factor: remoteRuntimeResourceFactor,
      enable_default_condenser: DEFAULT_SETTINGS.ENABLE_DEFAULT_CONDENSER,
    });
  } catch (error) {
    if (isAxiosError(error)) {
      const errorMessage = error.response?.data.error || error.message;
      return { error: errorMessage };
    }

    return { error: "An error occurred while saving settings" };
  }

  return { message: "Settings saved" };
};

function SettingsScreen() {
  const { settings, config } = useLoaderData<typeof clientLoader>();
  const settingsFetcher = useFetcher<typeof clientAction>();

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings.github_token_is_set;
  const isAnalyticsEnabled = settings.user_consents_to_analytics;
  const isAdvancedSettingsSet = hasAdvancedSettingsSet(settings);

  const [llmConfigMode, setLlmConfigMode] = React.useState<
    "basic" | "advanced"
  >(isAdvancedSettingsSet ? "advanced" : "basic");
  const [confirmationModeIsEnabled, setConfirmationModeIsEnabled] =
    React.useState(!!settings.security_analyzer);

  React.useEffect(() => {
    if (settingsFetcher.data?.message) {
      toast.success(settingsFetcher.data.message, {
        position: "top-right",
        style: {
          background: "#454545",
          border: "1px solid #717888",
          color: "#fff",
          borderRadius: "4px",
        },
      });
    } else if (settingsFetcher.data?.error) {
      toast.error(settingsFetcher.data.error, {
        position: "top-right",
        style: {
          background: "#454545",
          border: "1px solid #717888",
          color: "#fff",
          borderRadius: "4px",
        },
      });
    }
  }, [settingsFetcher.data]);

  return (
    <main className="bg-[#24272E] border border-[#454545] h-full rounded-xl">
      <settingsFetcher.Form method="POST" className="flex flex-col h-full">
        <header className="text-sm leading-6 px-3 py-1.5 border-b border-b-[#454545]">
          Settings
        </header>

        <div className="flex flex-col gap-6 grow overflow-y-auto px-11 py-9">
          <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
            Account Settings
          </h2>
          {isSaas && (
            <BrandButton type="button" variant="secondary">
              Configure GitHub Repositories
            </BrandButton>
          )}
          {!isSaas && (
            <>
              <SettingsInput
                testId="github-token-input"
                name="github-token-input"
                label="GitHub Token"
                type="password"
                className="w-[680px]"
              />

              <HelpLink
                testId="github-token-help-anchor"
                text="Get your token"
                linkText="here"
                href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
              />
            </>
          )}

          {isGitHubTokenSet && (
            <BrandButton type="button" variant="secondary">
              Disconnect from GitHub
            </BrandButton>
          )}

          <SettingsDropdown
            testId="language-input"
            name="language-input"
            label="Language"
            options={AvailableLanguages}
            defaultValue={settings.language}
            showOptionalTag
            className="w-[680px]"
          />

          <SettingsSwitch
            testId="enable-analytics-switch"
            name="enable-analytics-switch"
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
              name="llm-custom-model-input"
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
              name="base-url-input"
              label="Base URL"
              defaultValue={settings.llm_base_url}
              placeholder="https://api.openai.com"
              type="text"
              className="w-[680px]"
            />
          )}

          <SettingsInput
            testId="llm-api-key-input"
            name="llm-api-key-input"
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
              name="agent-input"
              label="Agent"
              defaultValue={settings.agent}
              type="text"
              className="w-[680px]"
            />
          )}

          {isSaas && llmConfigMode === "advanced" && (
            <SettingsInput
              testId="runtime-settings-input"
              name="runtime-settings-input"
              label="Runtime Settings"
              type="text"
              className="w-[680px]"
            />
          )}

          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="security-analyzer-input"
              name="security-analyzer-input"
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
          <BrandButton type="button" variant="secondary">
            Reset to defaults
          </BrandButton>
          <BrandButton type="submit" variant="primary">
            Save Changes
          </BrandButton>
        </footer>
      </settingsFetcher.Form>
    </main>
  );
}

export default SettingsScreen;
