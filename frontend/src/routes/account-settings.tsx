import React from "react";
import { Link } from "react-router";
import { BrandButton } from "#/components/features/settings/brand-button";
import { HelpLink } from "#/components/features/settings/help-link";
import { KeyStatusIcon } from "#/components/features/settings/key-status-icon";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { useAppLogout } from "#/hooks/use-app-logout";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { isCustomModel } from "#/utils/is-custom-model";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";

const REMOTE_RUNTIME_OPTIONS = [
  { key: 1, label: "1x (2 core, 8G)" },
  { key: 2, label: "2x (4 core, 16G)" },
];

function AccountSettings() {
  const {
    data: settings,
    isFetching: isFetchingSettings,
    isFetched,
    isSuccess: isSuccessfulSettings,
  } = useSettings();
  const { data: config } = useConfig();
  const {
    data: resources,
    isFetching: isFetchingResources,
    isSuccess: isSuccessfulResources,
  } = useAIConfigOptions();
  const { mutate: saveSettings } = useSaveSettings();
  const { handleLogout } = useAppLogout();

  const isFetching = isFetchingSettings || isFetchingResources;
  const isSuccess = isSuccessfulSettings && isSuccessfulResources;

  const determineWhetherToToggleAdvancedSettings = () => {
    if (isSuccess) {
      return (
        isCustomModel(resources.models, settings.LLM_MODEL) ||
        hasAdvancedSettingsSet(settings)
      );
    }

    return false;
  };

  const isSaas = config?.APP_MODE === "saas";
  const hasAppSlug = !!config?.APP_SLUG;
  const isGitHubTokenSet = settings?.GITHUB_TOKEN_IS_SET;
  const isLLMKeySet = settings?.LLM_API_KEY === "**********";
  const isAnalyticsEnabled = settings?.USER_CONSENTS_TO_ANALYTICS;
  const isAdvancedSettingsSet = determineWhetherToToggleAdvancedSettings();

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

  const formRef = React.useRef<HTMLFormElement>(null);

  const onSubmit = async (formData: FormData) => {
    const languageLabel = formData.get("language-input")?.toString();
    const languageValue = AvailableLanguages.find(
      ({ label }) => label === languageLabel,
    )?.value;

    const llmProvider = formData.get("llm-provider-input")?.toString();
    const llmModel = formData.get("llm-model-input")?.toString();
    const fullLlmModel = `${llmProvider}/${llmModel}`.toLowerCase();
    const customLlmModel = formData.get("llm-custom-model-input")?.toString();

    const rawRemoteRuntimeResourceFactor = formData
      .get("runtime-settings-input")
      ?.toString();
    const remoteRuntimeResourceFactor = REMOTE_RUNTIME_OPTIONS.find(
      ({ label }) => label === rawRemoteRuntimeResourceFactor,
    )?.key;

    const userConsentsToAnalytics =
      formData.get("enable-analytics-switch")?.toString() === "on";

    saveSettings(
      {
        github_token:
          formData.get("github-token-input")?.toString() || undefined,
        LANGUAGE: languageValue,
        user_consents_to_analytics: userConsentsToAnalytics,
        LLM_MODEL: customLlmModel || fullLlmModel,
        LLM_BASE_URL: formData.get("base-url-input")?.toString() || "",
        LLM_API_KEY:
          formData.get("llm-api-key-input")?.toString() ||
          (isLLMKeySet
            ? undefined // don't update if it's already set
            : ""), // reset if it's first time save to avoid 500 error
        AGENT: formData.get("agent-input")?.toString(),
        SECURITY_ANALYZER:
          formData.get("security-analyzer-input")?.toString() || "",
        REMOTE_RUNTIME_RESOURCE_FACTOR:
          remoteRuntimeResourceFactor ||
          DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
        CONFIRMATION_MODE: confirmationModeIsEnabled,
      },
      {
        onSuccess: () => {
          handleCaptureConsent(userConsentsToAnalytics);
          displaySuccessToast("Settings saved");
          setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
        },
        onError: (error) => {
          const errorMessage = retrieveAxiosErrorMessage(error);
          displayErrorToast(errorMessage);
        },
      },
    );
  };

  const handleReset = () => {
    saveSettings(
      {
        ...DEFAULT_SETTINGS,
        LLM_API_KEY: "", // reset LLM API key
      },
      {
        onSuccess: () => {
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

  if (isFetched && !settings) {
    return <div>Failed to fetch settings. Please try reloading.</div>;
  }

  const onToggleAdvancedMode = (isToggled: boolean) => {
    setLlmConfigMode(isToggled ? "advanced" : "basic");
    if (!isToggled) {
      // reset advanced state
      setConfirmationModeIsEnabled(!!settings?.SECURITY_ANALYZER);
    }
  };

  if (isFetching || !settings) {
    return (
      <div className="flex grow p-4">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <>
      <form
        ref={formRef}
        action={onSubmit}
        className="flex flex-col grow overflow-auto"
      >
        <div className="flex flex-col gap-12 px-11 py-9">
          <section className="flex flex-col gap-6">
            <div className="flex items-center gap-7">
              <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
                LLM Settings
              </h2>
              <SettingsSwitch
                testId="advanced-settings-switch"
                defaultIsToggled={isAdvancedSettingsSet}
                onToggle={onToggleAdvancedMode}
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
              className="w-[680px]"
              startContent={
                isLLMKeySet && <KeyStatusIcon isSet={isLLMKeySet} />
              }
              placeholder={isLLMKeySet ? "**********" : ""}
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
              <SettingsDropdownInput
                testId="runtime-settings-input"
                name="runtime-settings-input"
                label="Runtime Settings"
                items={REMOTE_RUNTIME_OPTIONS}
                defaultSelectedKey={settings.REMOTE_RUNTIME_RESOURCE_FACTOR?.toString()}
                isDisabled
                isClearable={false}
              />
            )}

            {llmConfigMode === "advanced" && (
              <SettingsSwitch
                testId="enable-confirmation-mode-switch"
                onToggle={setConfirmationModeIsEnabled}
                defaultIsToggled={!!settings.CONFIRMATION_MODE}
                isBeta
              >
                Enable confirmation mode
              </SettingsSwitch>
            )}
            {llmConfigMode === "advanced" && confirmationModeIsEnabled && (
              <div>
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
          </section>

          <section className="flex flex-col gap-6">
            <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
              GitHub Settings
            </h2>
            {isSaas && hasAppSlug && (
              <Link
                to={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
                target="_blank"
                rel="noreferrer noopener"
              >
                <BrandButton type="button" variant="secondary">
                  Configure GitHub Repositories
                </BrandButton>
              </Link>
            )}
            {!isSaas && (
              <>
                <SettingsInput
                  testId="github-token-input"
                  name="github-token-input"
                  label="GitHub Token"
                  type="password"
                  className="w-[680px]"
                  startContent={
                    isGitHubTokenSet && (
                      <KeyStatusIcon isSet={!!isGitHubTokenSet} />
                    )
                  }
                  placeholder={isGitHubTokenSet ? "**********" : ""}
                />

                <HelpLink
                  testId="github-token-help-anchor"
                  text="Get your token"
                  linkText="here"
                  href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
                />
              </>
            )}

            <BrandButton
              type="button"
              variant="secondary"
              onClick={handleLogout}
              isDisabled={!isGitHubTokenSet}
            >
              Disconnect from GitHub
            </BrandButton>
          </section>

          <section className="flex flex-col gap-6">
            <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
              Additional Settings
            </h2>

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
              defaultIsToggled={!!isAnalyticsEnabled}
            >
              Enable analytics
            </SettingsSwitch>
          </section>
        </div>
      </form>

      <footer className="flex gap-6 p-6 justify-end border-t border-t-tertiary">
        <BrandButton
          type="button"
          variant="secondary"
          onClick={() => setResetSettingsModalIsOpen(true)}
        >
          Reset to defaults
        </BrandButton>
        <BrandButton
          type="button"
          variant="primary"
          onClick={() => {
            formRef.current?.requestSubmit();
          }}
        >
          Save Changes
        </BrandButton>
      </footer>

      {resetSettingsModalIsOpen && (
        <ModalBackdrop>
          <div
            data-testid="reset-modal"
            className="bg-base p-4 rounded-xl flex flex-col gap-4"
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
    </>
  );
}

export default AccountSettings;
