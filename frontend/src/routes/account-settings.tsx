import { BrandButton } from "#/components/features/settings/brand-button";
import { HelpLink } from "#/components/features/settings/help-link";
import { KeyStatusIcon } from "#/components/features/settings/key-status-icon";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { isCustomModel } from "#/utils/is-custom-model";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { Modal, ModalBody, ModalContent, Tab, Tabs } from "@heroui/react";
import React from "react";
import { useNavigate } from "react-router";

const REMOTE_RUNTIME_OPTIONS = [
  { key: 1, label: "1x (2 core, 8G)" },
  { key: 2, label: "2x (4 core, 16G)" },
];

const AccountSettings = () => {
  const navigate = useNavigate();
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

  const isFetching = isFetchingSettings || isFetchingResources;
  console.log("isFetching", isFetching);
  const isSuccess = isSuccessfulSettings && isSuccessfulResources;
  const isSaas = config?.APP_MODE === "saas";
  const shouldHandleSpecialSaasCase =
    config?.FEATURE_FLAGS.HIDE_LLM_SETTINGS && isSaas;

  const determineWhetherToToggleAdvancedSettings = () => {
    if (shouldHandleSpecialSaasCase) return true;
    if (isSuccess) {
      return (
        isCustomModel(resources.models, settings?.LLM_MODEL || "") ||
        hasAdvancedSettingsSet({
          ...settings,
          PROVIDER_TOKENS: settings?.PROVIDER_TOKENS || {
            github: "",
            gitlab: "",
          },
        } as any)
      );
    }
    return false;
  };

  const isLLMKeySet = settings?.LLM_API_KEY === "**********";
  const isAnalyticsEnabled = settings?.USER_CONSENTS_TO_ANALYTICS;
  const isAdvancedSettingsSet = determineWhetherToToggleAdvancedSettings();

  const modelsAndProviders = organizeModelsAndProviders(
    resources?.models || [],
  );

  const [llmConfigMode, setLlmConfigMode] = React.useState(
    isAdvancedSettingsSet ? "advanced" : "basic",
  );
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
    const enableMemoryCondenser =
      formData.get("enable-memory-condenser-switch")?.toString() === "on";
    const enableSoundNotifications =
      formData.get("enable-sound-notifications-switch")?.toString() === "on";
    const llmBaseUrl = formData.get("base-url-input")?.toString() || "";
    const llmApiKey =
      formData.get("llm-api-key-input")?.toString() ||
      (isLLMKeySet ? undefined : "");

    const finalLlmModel = shouldHandleSpecialSaasCase
      ? undefined
      : customLlmModel || fullLlmModel;
    const finalLlmBaseUrl = shouldHandleSpecialSaasCase
      ? undefined
      : llmBaseUrl;
    const finalLlmApiKey = shouldHandleSpecialSaasCase ? undefined : llmApiKey;

    const githubToken = formData.get("github-token-input")?.toString();
    const newSettings = {
      github_token: githubToken,
      provider_tokens: githubToken
        ? { github: githubToken, gitlab: "" }
        : undefined,
      LANGUAGE: languageValue,
      user_consents_to_analytics: userConsentsToAnalytics,
      ENABLE_DEFAULT_CONDENSER: enableMemoryCondenser,
      ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
      LLM_MODEL: finalLlmModel,
      LLM_BASE_URL: finalLlmBaseUrl,
      LLM_API_KEY: finalLlmApiKey,
      AGENT: formData.get("agent-input")?.toString(),
      SECURITY_ANALYZER:
        formData.get("security-analyzer-input")?.toString() || "",
      REMOTE_RUNTIME_RESOURCE_FACTOR:
        remoteRuntimeResourceFactor ||
        DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
      CONFIRMATION_MODE: confirmationModeIsEnabled,
    };

    saveSettings(newSettings, {
      onSuccess: () => {
        handleCaptureConsent(userConsentsToAnalytics);
        displaySuccessToast("Settings saved");
        setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
      },
      onError: (error) => {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage);
      },
    });
  };

  const handleReset = () => {
    saveSettings(null, {
      onSuccess: () => {
        displaySuccessToast("Settings reset");
        setResetSettingsModalIsOpen(false);
        setLlmConfigMode("basic");
      },
    });
  };

  React.useEffect(() => {
    setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
  }, [isAdvancedSettingsSet]);

  if (isFetched && !settings) {
    return (
      <div className="text-white">
        Failed to fetch settings. Please try reloading.
      </div>
    );
  }

  if (isFetching || !settings) {
    return (
      <div className="flex items-center justify-center grow p-4">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <>
      <form
        ref={formRef}
        action={onSubmit}
        className="flex flex-col grow overflow-auto p-3 md:p-6"
      >
        <div className="max-w-[680px]">
          {/* {!shouldHandleSpecialSaasCase && (
            <section className="flex flex-col gap-6">
              <h3 className="text-[18px] font-semibold text-[#EFEFEF]">
                LLM Settings
              </h3>
              <Tabs
                selectedKey={llmConfigMode}
                onSelectionChange={(key: any) => setLlmConfigMode(key)}
                classNames={{
                  base: "w-full",
                  tabList: "rounded-[12px]",
                  cursor: "bg-[#080808] rounded-lg",
                  tabContent:
                    "text-[14px] font-semibold text-[#595B57] group-data-[selected=true]:text-[#EFEFEF] ",
                }}
              >
                <Tab key="basic" title="Basic" />
                <Tab key="advanced" title="Advanced" />
              </Tabs>
              {llmConfigMode === "basic" && (
                <ModelSelector
                  models={modelsAndProviders}
                  currentModel={settings.LLM_MODEL}
                />
              )}
              {llmConfigMode === "advanced" && (
                <>
                  <SettingsInput
                    testId="llm-custom-model-input"
                    name="llm-custom-model-input"
                    label="Custom Model"
                    defaultValue={settings.LLM_MODEL}
                    placeholder="anthropic/claude-3-5-sonnet-20241022"
                    type="text"
                    className="w-full"
                  />
                  <SettingsInput
                    testId="base-url-input"
                    name="base-url-input"
                    label="Base URL"
                    defaultValue={settings.LLM_BASE_URL}
                    placeholder="https://api.openai.com"
                    type="text"
                    className="w-full"
                  />
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
                  {isSaas && (
                    <SettingsDropdownInput
                      testId="runtime-settings-input"
                      name="runtime-settings-input"
                      label={
                        <>
                          Runtime Settings (
                          <a
                            href="mailto:contact@all-hands.dev"
                            className="text-orange-500"
                          >
                            get in touch for access
                          </a>
                          )
                        </>
                      }
                      items={REMOTE_RUNTIME_OPTIONS}
                      defaultSelectedKey={settings.REMOTE_RUNTIME_RESOURCE_FACTOR?.toString()}
                      isDisabled
                      isClearable={false}
                    />
                  )}
                  <div className="flex flex-col md:flex-row md:items-center gap-8">
                    <SettingsSwitch
                      testId="enable-confirmation-mode-switch"
                      onToggle={setConfirmationModeIsEnabled}
                      defaultIsToggled={!!settings.CONFIRMATION_MODE}
                      isBeta
                    >
                      Enable confirmation mode
                    </SettingsSwitch>
                    <SettingsSwitch
                      testId="enable-memory-condenser-switch"
                      name="enable-memory-condenser-switch"
                      defaultIsToggled={!!settings.ENABLE_DEFAULT_CONDENSER}
                    >
                      Enable memory condensation
                    </SettingsSwitch>
                  </div>
                  {confirmationModeIsEnabled && (
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
                  )}
                </>
              )}

              <div className="relative ">
                <SettingsInput
                  testId="llm-api-key-input"
                  name="llm-api-key-input"
                  label="API Key"
                  type="password"
                  className="w-full"
                  startContent={
                    isLLMKeySet && <KeyStatusIcon isSet={isLLMKeySet} />
                  }
                  placeholder={isLLMKeySet ? "<hidden>" : "Enter"}
                />
                <div className="absolute top-0 right-0">
                  <HelpLink
                    testId="llm-api-key-help-anchor"
                    // text="Don't know your API key?"
                    text=""
                    linkText="Click here for instructions"
                    href="https://docs.all-hands.dev/modules/usage/installation#getting-an-api-key"
                    classNames={{
                      linkText: "text-[#FF6100]",
                    }}
                  />
                </div>
              </div>
            </section>
          )}
          <div className="my-7 h-[1px] w-full bg-[#1B1C1A]" /> */}
          <section className="flex flex-col gap-6">
            <h3 className="text-[18px] font-semibold text-[#EFEFEF]">
              Additional Settings
            </h3>
            <SettingsDropdownInput
              testId="language-input"
              name="language-input"
              label="Language"
              items={AvailableLanguages.map((language) => ({
                key: language.value,
                label: language.label,
              }))}
              defaultSelectedKey={settings?.LANGUAGE}
              isClearable={false}
            />
            <div className="flex flex-col md:flex-row md:items-center gap-8">
              <SettingsSwitch
                testId="enable-analytics-switch"
                name="enable-analytics-switch"
                defaultIsToggled={!!isAnalyticsEnabled}
              >
                Enable analytics
              </SettingsSwitch>
              <SettingsSwitch
                testId="enable-sound-notifications-switch"
                name="enable-sound-notifications-switch"
                defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
              >
                Enable sound notifications
              </SettingsSwitch>
            </div>
          </section>
        </div>
      </form>
      <footer className="flex justify-end gap-4 w-full px-3 py-2 md:p-6 md:py-4 border-t border-t-[#232521] bg-[#080808] rounded-b-xl">
        <BrandButton
          type="button"
          variant="secondary"
          onClick={() => setResetSettingsModalIsOpen(true)}
          className="bg-[#1E1E1F] text-[14px] font-semibold text-[#EFEFEF] px-4 py-[10px] rounded-lg border-[0px]"
        >
          Reset to defaults
        </BrandButton>
        <BrandButton
          type="button"
          variant="primary"
          onClick={() => formRef.current?.requestSubmit()}
          className="bg-primary text-[14px] font-semibold text-[#080808] px-4 py-[10px] rounded-lg border-[0px]"
        >
          Save Changes
        </BrandButton>
      </footer>
      {resetSettingsModalIsOpen && (
        <Modal
          isOpen={resetSettingsModalIsOpen}
          onClose={() => setResetSettingsModalIsOpen(false)}
          classNames={{
            backdrop: "bg-black/40 backdrop-blur-[12px]",
            base: "bg-[#0F0F0F] max-w-[559px] rounded-2xl w-full",
          }}
        >
          <ModalContent>
            <ModalBody className="p-6">
              <p className="text-[#EFEFEF] mb-4 text-[16px] font-semibold">
                Are you sure you want to reset all settings?
              </p>
              <div className="flex gap-2">
                <BrandButton
                  type="button"
                  variant="primary"
                  onClick={handleReset}
                  className="bg-primary text-[14px] font-semibold text-[#080808] px-4 py-[10px] rounded-lg flex-1 border-[0px]"
                >
                  Reset
                </BrandButton>
                <BrandButton
                  type="button"
                  variant="secondary"
                  onClick={() => setResetSettingsModalIsOpen(false)}
                  className="bg-[#1E1E1F] text-[14px] font-semibold text-[#EFEFEF] px-4 py-[10px] rounded-lg flex-1 border-[0px]"
                >
                  Cancel
                </BrandButton>
              </div>
            </ModalBody>
          </ModalContent>
        </Modal>
      )}
    </>
  );
};

export default AccountSettings;
