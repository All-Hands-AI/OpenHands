import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
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
import { ProviderOptions } from "#/types/settings";
import { useAuth } from "#/context/auth-context";
import { useAppLogout } from "#/hooks/use-app-logout";

// Define REMOTE_RUNTIME_OPTIONS for testing
const REMOTE_RUNTIME_OPTIONS = [
  { key: "1", label: "Standard" },
  { key: "2", label: "Enhanced" },
  { key: "4", label: "Premium" },
];

function AccountSettings() {
  const navigate = useNavigate();
  const { t } = useTranslation();
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
  const { providerTokensSet, providersAreSet } = useAuth();

  const isFetching = isFetchingSettings || isFetchingResources;
  console.log("isFetching", isFetching);
  const isSuccess = isSuccessfulSettings && isSuccessfulResources;
  const isSaas = config?.APP_MODE === "saas";
  const shouldHandleSpecialSaasCase =
    config?.FEATURE_FLAGS.HIDE_LLM_SETTINGS && isSaas;

  const determineWhetherToToggleAdvancedSettings = () => {
    return true
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

  // TODO FIXME: unclear whether this is a good conflict
  // const isLLMKeySet = settings?.LLM_API_KEY === "**********";
  const hasAppSlug = !!config?.APP_SLUG;
  const isGitHubTokenSet =
    providerTokensSet.includes(ProviderOptions.github) || false;
  const isGitLabTokenSet =
    providerTokensSet.includes(ProviderOptions.gitlab) || false;
  const isLLMKeySet = settings?.LLM_API_KEY_SET;
  const isAnalyticsEnabled = settings?.USER_CONSENTS_TO_ANALYTICS;
  const isAdvancedSettingsSet = determineWhetherToToggleAdvancedSettings();

  const modelsAndProviders = organizeModelsAndProviders(
    resources?.models || [],
  );

  const [llmConfigMode, setLlmConfigMode] = React.useState(
    // TODO: uncomment this when the advanced settings are ready
    // isAdvancedSettingsSet ? "advanced" : "basic",
    'basic',
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
    const inputApiKey = formData.get("llm-api-key-input")?.toString() || "";
    const llmApiKey =
      formData.get("llm-api-key-input")?.toString() ||
      (isLLMKeySet ? undefined : "");

      inputApiKey === "" && isLLMKeySet
        ? undefined // don't update if it's already set and input is empty
        : inputApiKey; // otherwise use the input value

    const githubToken = formData.get("github-token-input")?.toString();
    const gitlabToken = formData.get("gitlab-token-input")?.toString();
    // we don't want the user to be able to modify these settings in SaaS
    const finalLlmModel = shouldHandleSpecialSaasCase
      ? undefined
      : customLlmModel || fullLlmModel;
    const finalLlmBaseUrl = shouldHandleSpecialSaasCase
      ? undefined
      : llmBaseUrl;
    const finalLlmApiKey = shouldHandleSpecialSaasCase ? undefined : llmApiKey;

    const newSettings = {
      provider_tokens:
        githubToken || gitlabToken
          ? {
              github: githubToken || "",
              gitlab: gitlabToken || "",
            }
          : undefined,
      LANGUAGE: languageValue,
      user_consents_to_analytics: userConsentsToAnalytics,
      ENABLE_DEFAULT_CONDENSER: enableMemoryCondenser,
      ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
      LLM_MODEL: finalLlmModel,
      LLM_BASE_URL: finalLlmBaseUrl,
      llm_api_key: finalLlmApiKey,
      AGENT: formData.get("agent-input")?.toString(),
      SECURITY_ANALYZER:
        formData.get("security-analyzer-input")?.toString() || "",
      REMOTE_RUNTIME_RESOURCE_FACTOR:
        remoteRuntimeResourceFactor !== null
          ? Number(remoteRuntimeResourceFactor)
          : DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
      CONFIRMATION_MODE: confirmationModeIsEnabled,
    };

    saveSettings(newSettings, {
      onSuccess: () => {
        handleCaptureConsent(userConsentsToAnalytics);
        displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
        setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
      },
      onError: (error) => {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
      },
    });
  };

  const handleReset = () => {
    saveSettings(null, {
      onSuccess: () => {
        displaySuccessToast(t(I18nKey.SETTINGS$RESET));
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
          {!shouldHandleSpecialSaasCase && (
            <section className="flex flex-col gap-6">
            <h3 className="text-[18px] font-semibold text-neutral-100 dark:text-[#EFEFEF]">
                LLM Settings
            </h3>
              {/* <Tabs
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
              </Tabs> */}
              {llmConfigMode === "basic" && (
                <ModelSelector
                  models={modelsAndProviders}
                  currentModel={settings.LLM_MODEL}
                />
              )}
              {llmConfigMode === "advanced" && (
                <>
                  {/* <SettingsInput
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
                  /> */}
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
                  {/* TODO: enable later when allow custom setting */}
                  {/* <div className="flex flex-col md:flex-row md:items-center gap-8">
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
                  </div> */}
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

              {/* TODO: enable later when allow custom setting */}
              {/* <div className="relative ">
                <SettingsInput
                  testId="llm-api-key-input"
                  name="llm-api-key-input"
                  label={t(I18nKey.SETTINGS_FORM$API_KEY)}
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
              </div> */}
            </section>
          )}
          <div className="my-7 h-[1px] w-full bg-[#1B1C1A]" />
          <section className="flex flex-col gap-6">
            <h3 className="text-[18px] font-semibold text-neutral-100 dark:text-[#EFEFEF]">
              Additional Settings
            </h3>
            <SettingsDropdownInput
              testId="language-input"
              name="language-input"
              label={t(I18nKey.SETTINGS$LANGUAGE)}
              items={AvailableLanguages.map((language) => ({
                key: language.value,
                label: language.label,
              }))}
              defaultSelectedKey={settings?.LANGUAGE}
              isClearable={false}
            />
            <div className="flex flex-col md:flex-row md:items-center gap-8">
              {/* <SettingsSwitch
                testId="enable-analytics-switch"
                name="enable-analytics-switch"
                defaultIsToggled={!!isAnalyticsEnabled}
              >
                Enable analytics
              </SettingsSwitch> */}
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
      <footer className="flex justify-end gap-4 w-full px-3 py-2 md:p-6 md:py-4 border-t border-t-neutral-1000 dark:border-t-[#232521] bg-neutral-1100 dark:bg-[#080808] rounded-b-xl">
        <BrandButton
          type="button"
          variant="secondary"
          onClick={() => setResetSettingsModalIsOpen(true)}
          className="bg-[#1E1E1F] text-[14px] font-semibold text-[#EFEFEF] px-4 py-[10px] rounded-lg border-[0px]"
        >
          {t(I18nKey.BUTTON$RESET_TO_DEFAULTS)}
        </BrandButton>
        <BrandButton
          type="button"
          variant="primary"
          onClick={() => formRef.current?.requestSubmit()}
          className="bg-primary text-[14px] font-semibold text-[#080808] px-4 py-[10px] rounded-lg border-[0px]"
        >
          {t(I18nKey.BUTTON$SAVE)}
        </BrandButton>
      </footer>
      {resetSettingsModalIsOpen && (
        <Modal
          isOpen={resetSettingsModalIsOpen}
          onClose={() => setResetSettingsModalIsOpen(false)}
          classNames={{
            backdrop: "bg-black/40 backdrop-blur-[12px]",
            base: "bg-white dark:bg-[#0F0F0F] max-w-[559px] rounded-2xl w-full",
          }}
        >
          <ModalContent>
            <ModalBody className="p-6">
              <p className="text-neutral-100 dark:text-content mb-4 text-[16px] font-semibold">
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
