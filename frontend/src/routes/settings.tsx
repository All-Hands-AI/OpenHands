import React from "react";
import toast from "react-hot-toast";
import { isAxiosError } from "axios";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { HelpLink } from "#/components/features/settings/help-link";
import { AvailableLanguages } from "#/i18n";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { useSettings } from "#/hooks/query/use-settings";
import { useConfig } from "#/hooks/query/use-config";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { useAppLogout } from "#/hooks/use-app-logout";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";

const displayErrorToast = (error: string) => {
  toast.error(error, {
    position: "top-right",
    style: {
      background: "#454545",
      border: "1px solid #717888",
      color: "#fff",
      borderRadius: "4px",
    },
  });
};

const displaySuccessToast = (message: string) => {
  toast.success(message, {
    position: "top-right",
    style: {
      background: "#454545",
      border: "1px solid #717888",
      color: "#fff",
      borderRadius: "4px",
    },
  });
};

function SettingsScreen() {
  const { data: settings, isFetching, isSuccess } = useSettings();
  const { data: config } = useConfig();
  const { data: resources } = useAIConfigOptions();
  const { mutateAsync: saveSettings } = useSaveSettings();
  const { handleLogout } = useAppLogout();

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings?.GITHUB_TOKEN_IS_SET;
  const isLLMKeySet = settings?.LLM_API_KEY === "**********";
  const isAnalyticsEnabled = settings?.USER_CONSENTS_TO_ANALYTICS;
  const isAdvancedSettingsSet = settings
    ? hasAdvancedSettingsSet(settings)
    : false;

  const modelsAndProviders = organizeModelsAndProviders(
    resources?.models || [],
  );

  const [llmConfigMode, setLlmConfigMode] = React.useState<
    "basic" | "advanced"
  >(isAdvancedSettingsSet ? "advanced" : "basic");
  const [confirmationModeIsEnabled, setConfirmationModeIsEnabled] =
    React.useState(!!settings?.SECURITY_ANALYZER);
  const [resetSettingsModalIsOpen, setResetSettingsModalIsOpen] =
    React.useState(false);

  const formAction = async (formData: FormData) => {
    const languageLabel = formData.get("language-input")?.toString();
    const languageValue = AvailableLanguages.find(
      ({ label }) => label === languageLabel,
    )?.value;

    const llmProvider = formData.get("llm-provider-input")?.toString();
    const llmModel = formData.get("llm-model-input")?.toString();
    const fullLlmModel = `${llmProvider}/${llmModel}`.toLowerCase();
    const customLlmModel = formData.get("llm-custom-model-input")?.toString();

    const rawRemoteRuntimeResourceFactor =
      formData.get("runtime-settings-input")?.toString() ||
      DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR;
    const remoteRuntimeResourceFactor = Number(rawRemoteRuntimeResourceFactor);

    const userConsentsToAnalytics =
      formData.get("enable-analytics-switch")?.toString() === "on";

    try {
      await saveSettings(
        {
          github_token: formData.get("github-token-input")?.toString() || "",
          LANGUAGE: languageValue,
          user_consents_to_analytics: userConsentsToAnalytics,
          LLM_MODEL: customLlmModel || fullLlmModel,
          LLM_BASE_URL: formData.get("base-url-input")?.toString() || "",
          LLM_API_KEY: formData.get("llm-api-key-input")?.toString(),
          AGENT: formData.get("agent-input")?.toString(),
          SECURITY_ANALYZER:
            formData.get("security-analyzer-input")?.toString() || "",
          REMOTE_RUNTIME_RESOURCE_FACTOR: remoteRuntimeResourceFactor,
          ENABLE_DEFAULT_CONDENSER: DEFAULT_SETTINGS.ENABLE_DEFAULT_CONDENSER,
        },
        {
          onSuccess: () => {
            handleCaptureConsent(userConsentsToAnalytics);
            displaySuccessToast("Settings saved");
            setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
          },
        },
      );
    } catch (error) {
      if (isAxiosError(error)) {
        const errorMessage = error.response?.data.error || error.message;
        displayErrorToast(errorMessage);
      }

      displayErrorToast("An error occurred while saving settings");
    }
  };

  const handleReset = () => {
    saveSettings(
      {
        ...DEFAULT_SETTINGS,
        user_consents_to_analytics: DEFAULT_SETTINGS.USER_CONSENTS_TO_ANALYTICS,
      },
      {
        onSuccess: () => {
          handleCaptureConsent(!!DEFAULT_SETTINGS.USER_CONSENTS_TO_ANALYTICS);
          displaySuccessToast("Settings reset");
          setResetSettingsModalIsOpen(false);
          setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
        },
      },
    );
  };

  React.useEffect(() => {
    // If settings is still loading by the time the state is set, it will always
    // default to basic settings. This is a workaround to ensure the correct
    // settings are displayed.
    setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
  }, [isAdvancedSettingsSet]);

  if (isFetching) {
    return <div>Loading...</div>;
  }

  if (!isSuccess) {
    return <div>Failed to fetch settings. Please try reloading.</div>;
  }

  return (
    <main
      data-testid="settings-screen"
      className="bg-[#24272E] border border-[#454545] h-full rounded-xl"
    >
      <form action={formAction} className="flex flex-col h-full">
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
          {!isSaas && !isGitHubTokenSet && (
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
            <BrandButton
              type="button"
              variant="secondary"
              onClick={handleLogout}
            >
              Disconnect from GitHub
            </BrandButton>
          )}

          <SettingsDropdownInput
            testId="language-input"
            name="language-input"
            label="Language"
            items={AvailableLanguages.map((language) => ({
              key: language.value,
              label: language.label,
            }))}
            defaultSelectedKey={settings.LANGUAGE}
            isClearable={false}
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
            <ModelSelector
              models={modelsAndProviders}
              currentModel={settings.LLM_MODEL}
            />
          )}

          {llmConfigMode === "advanced" && (
            <SettingsInput
              testId="llm-custom-model-input"
              name="llm-custom-model-input"
              label="Custom Model"
              defaultValue={settings.LLM_MODEL}
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
              defaultValue={settings.LLM_BASE_URL}
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
            badgeContent={isLLMKeySet ? "SET" : undefined}
            className="w-[680px]"
          />

          <HelpLink
            testId="llm-api-key-help-anchor"
            text="Don't know your API key?"
            linkText="Click here for instructions"
            href="https://docs.all-hands.dev/modules/usage/llms"
          />

          {llmConfigMode === "advanced" && (
            <SettingsDropdownInput
              testId="agent-input"
              name="agent-input"
              label="Agent"
              items={
                resources?.agents.map((agent) => ({
                  key: agent,
                  label: agent,
                })) || []
              }
              defaultSelectedKey={settings.AGENT}
              isClearable={false}
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
            <SettingsSwitch
              testId="enable-confirmation-mode-switch"
              onToggle={setConfirmationModeIsEnabled}
              defaultIsToggled={!!settings.SECURITY_ANALYZER}
            >
              Enable confirmation mode
            </SettingsSwitch>
          )}
          {llmConfigMode === "advanced" && confirmationModeIsEnabled && (
            <div className="peer-has-checked:hidden">
              <SettingsDropdownInput
                testId="security-analyzer-input"
                name="security-analyzer-input"
                label="Security Analyzer"
                items={
                  resources?.securityAnalyzers.map((analyzer) => ({
                    key: analyzer,
                    label: analyzer,
                  })) || []
                }
                defaultSelectedKey={settings.SECURITY_ANALYZER}
                isClearable
                showOptionalTag
              />
            </div>
          )}
        </div>

        <footer className="flex gap-6 p-6 justify-end border-t border-t-[#454545]">
          <BrandButton
            type="button"
            variant="secondary"
            onClick={() => setResetSettingsModalIsOpen(true)}
          >
            Reset to defaults
          </BrandButton>
          <BrandButton type="submit" variant="primary">
            Save Changes
          </BrandButton>
        </footer>
      </form>

      {resetSettingsModalIsOpen && (
        <ModalBackdrop>
          <div
            data-testid="reset-modal"
            className="bg-root-primary p-4 rounded-xl flex flex-col gap-4"
          >
            <p>Are you sure you want to reset all settings?</p>
            <div className="w-full flex gap-2">
              <BrandButton
                type="button"
                variant="primary"
                className="grow"
                onClick={() => {
                  handleReset();
                }}
              >
                Reset
              </BrandButton>

              <BrandButton
                type="button"
                variant="secondary"
                className="grow"
                onClick={() => {
                  setResetSettingsModalIsOpen(false);
                }}
              >
                Cancel
              </BrandButton>
            </div>
          </div>
        </ModalBackdrop>
      )}
    </main>
  );
}

export default SettingsScreen;
