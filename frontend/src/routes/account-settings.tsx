import React from "react";
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
import { ProviderOptions } from "#/types/settings";
import { useAuth } from "#/context/auth-context";

// Define REMOTE_RUNTIME_OPTIONS for testing
const REMOTE_RUNTIME_OPTIONS = [
  { key: "1", label: "Standard" },
  { key: "2", label: "Enhanced" },
  { key: "4", label: "Premium" },
];

function AccountSettings() {
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
  const isSuccess = isSuccessfulSettings && isSuccessfulResources;

  const isSaas = config?.APP_MODE === "saas";
  const shouldHandleSpecialSaasCase =
    config?.FEATURE_FLAGS.HIDE_LLM_SETTINGS && isSaas;

  const determineWhetherToToggleAdvancedSettings = () => {
    if (shouldHandleSpecialSaasCase) return true;

    if (isSuccess) {
      return (
        isCustomModel(resources.models, settings.LLM_MODEL) ||
        hasAdvancedSettingsSet({
          ...settings,
        })
      );
    }

    return false;
  };

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
    const enableMemoryCondenser =
      formData.get("enable-memory-condenser-switch")?.toString() === "on";
    const enableSoundNotifications =
      formData.get("enable-sound-notifications-switch")?.toString() === "on";
    const llmBaseUrl = formData.get("base-url-input")?.toString().trim() || "";
    const inputApiKey = formData.get("llm-api-key-input")?.toString() || "";
    const llmApiKey =
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
        data-testid="account-settings-form"
        ref={formRef}
        action={onSubmit}
        className="flex flex-col grow overflow-auto"
      >
        <div className="flex flex-col gap-12 px-11 py-9">
          {!shouldHandleSpecialSaasCase && (
            <section
              data-testid="llm-settings-section"
              className="flex flex-col gap-6"
            >
              <div className="flex items-center gap-7">
                <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
                  {t(I18nKey.SETTINGS$LLM_SETTINGS)}
                </h2>
                {!shouldHandleSpecialSaasCase && (
                  <SettingsSwitch
                    testId="advanced-settings-switch"
                    defaultIsToggled={isAdvancedSettingsSet}
                    onToggle={onToggleAdvancedMode}
                  >
                    {t(I18nKey.SETTINGS$ADVANCED)}
                  </SettingsSwitch>
                )}
              </div>

              {llmConfigMode === "basic" && !shouldHandleSpecialSaasCase && (
                <ModelSelector
                  models={modelsAndProviders}
                  currentModel={settings.LLM_MODEL}
                />
              )}

              {llmConfigMode === "advanced" && !shouldHandleSpecialSaasCase && (
                <SettingsInput
                  testId="llm-custom-model-input"
                  name="llm-custom-model-input"
                  label={t(I18nKey.SETTINGS$CUSTOM_MODEL)}
                  defaultValue={settings.LLM_MODEL}
                  placeholder="anthropic/claude-3-5-sonnet-20241022"
                  type="text"
                  className="w-[680px]"
                />
              )}
              {llmConfigMode === "advanced" && !shouldHandleSpecialSaasCase && (
                <SettingsInput
                  testId="base-url-input"
                  name="base-url-input"
                  label={t(I18nKey.SETTINGS$BASE_URL)}
                  defaultValue={settings.LLM_BASE_URL}
                  placeholder="https://api.openai.com"
                  type="text"
                  className="w-[680px]"
                />
              )}

              {!shouldHandleSpecialSaasCase && (
                <SettingsInput
                  testId="llm-api-key-input"
                  name="llm-api-key-input"
                  label={t(I18nKey.SETTINGS_FORM$API_KEY)}
                  type="password"
                  className="w-[680px]"
                  placeholder={isLLMKeySet ? "<hidden>" : ""}
                  startContent={
                    isLLMKeySet && <KeyStatusIcon isSet={isLLMKeySet} />
                  }
                />
              )}

              {!shouldHandleSpecialSaasCase && (
                <HelpLink
                  testId="llm-api-key-help-anchor"
                  text={t(I18nKey.SETTINGS$DONT_KNOW_API_KEY)}
                  linkText={t(I18nKey.SETTINGS$CLICK_FOR_INSTRUCTIONS)}
                  href="https://docs.all-hands.dev/modules/usage/installation#getting-an-api-key"
                />
              )}

              {llmConfigMode === "advanced" && (
                <SettingsDropdownInput
                  testId="agent-input"
                  name="agent-input"
                  label={t(I18nKey.SETTINGS$AGENT)}
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
                  label={
                    <>
                      {t(I18nKey.SETTINGS$RUNTIME_SETTINGS)}
                      <a href="mailto:contact@all-hands.dev">
                        {t(I18nKey.SETTINGS$GET_IN_TOUCH)}
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

              {llmConfigMode === "advanced" && (
                <SettingsSwitch
                  testId="enable-confirmation-mode-switch"
                  onToggle={setConfirmationModeIsEnabled}
                  defaultIsToggled={!!settings.CONFIRMATION_MODE}
                  isBeta
                >
                  {t(I18nKey.SETTINGS$CONFIRMATION_MODE)}
                </SettingsSwitch>
              )}

              {llmConfigMode === "advanced" && (
                <SettingsSwitch
                  testId="enable-memory-condenser-switch"
                  name="enable-memory-condenser-switch"
                  defaultIsToggled={!!settings.ENABLE_DEFAULT_CONDENSER}
                >
                  {t(I18nKey.SETTINGS$ENABLE_MEMORY_CONDENSATION)}
                </SettingsSwitch>
              )}

              {llmConfigMode === "advanced" && confirmationModeIsEnabled && (
                <div>
                  <SettingsDropdownInput
                    testId="security-analyzer-input"
                    name="security-analyzer-input"
                    label={t(I18nKey.SETTINGS$SECURITY_ANALYZER)}
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
          )}

          <section className="flex flex-col gap-6">
            <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
              {t(I18nKey.SETTINGS$GITHUB_SETTINGS)}
            </h2>
            {isSaas && hasAppSlug && (
              <Link
                to={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
                target="_blank"
                rel="noreferrer noopener"
              >
                <BrandButton type="button" variant="secondary">
                  {t(I18nKey.GITHUB$CONFIGURE_REPOS)}
                </BrandButton>
              </Link>
            )}
            {!isSaas && (
              <>
                <SettingsInput
                  testId="github-token-input"
                  name="github-token-input"
                  label={t(I18nKey.GITHUB$TOKEN_LABEL)}
                  type="password"
                  className="w-[680px]"
                  startContent={
                    isGitHubTokenSet && (
                      <KeyStatusIcon isSet={!!isGitHubTokenSet} />
                    )
                  }
                  placeholder={isGitHubTokenSet ? "<hidden>" : ""}
                />
                <p data-testid="github-token-help-anchor" className="text-xs">
                  {" "}
                  {t(I18nKey.GITHUB$GET_TOKEN)}{" "}
                  <b>
                    {" "}
                    <a
                      href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
                      target="_blank"
                      className="underline underline-offset-2"
                      rel="noopener noreferrer"
                    >
                      GitHub
                    </a>{" "}
                  </b>
                  {t(I18nKey.COMMON$HERE)}{" "}
                  <b>
                    <a
                      href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
                      target="_blank"
                      className="underline underline-offset-2"
                      rel="noopener noreferrer"
                    >
                      {t(I18nKey.COMMON$CLICK_FOR_INSTRUCTIONS)}
                    </a>
                  </b>
                  .
                </p>

                <SettingsInput
                  testId="gitlab-token-input"
                  name="gitlab-token-input"
                  label={t(I18nKey.GITLAB$TOKEN_LABEL)}
                  type="password"
                  className="w-[680px]"
                  startContent={
                    isGitLabTokenSet && (
                      <KeyStatusIcon isSet={!!isGitLabTokenSet} />
                    )
                  }
                  placeholder={isGitHubTokenSet ? "<hidden>" : ""}
                />

                <p data-testid="gitlab-token-help-anchor" className="text-xs">
                  {" "}
                  {t(I18nKey.GITLAB$GET_TOKEN)}{" "}
                  <b>
                    {" "}
                    <a
                      href="https://gitlab.com/-/user_settings/personal_access_tokens?name=openhands-app&scopes=api,read_user,read_repository,write_repository"
                      target="_blank"
                      className="underline underline-offset-2"
                      rel="noopener noreferrer"
                    >
                      GitLab
                    </a>{" "}
                  </b>
                  {t(I18nKey.GITLAB$OR_SEE)}{" "}
                  <b>
                    <a
                      href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
                      target="_blank"
                      className="underline underline-offset-2"
                      rel="noopener noreferrer"
                    >
                      {t(I18nKey.COMMON$DOCUMENTATION)}
                    </a>
                  </b>
                  .
                </p>
                <BrandButton
                  type="button"
                  variant="secondary"
                  onClick={handleLogout}
                  isDisabled={!providersAreSet}
                >
                  Disconnect Tokens
                </BrandButton>
              </>
            )}
          </section>

          <section className="flex flex-col gap-6">
            <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
              {t(I18nKey.ACCOUNT_SETTINGS$ADDITIONAL_SETTINGS)}
            </h2>

            <SettingsDropdownInput
              testId="language-input"
              name="language-input"
              label={t(I18nKey.SETTINGS$LANGUAGE)}
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
              {t(I18nKey.ANALYTICS$ENABLE)}
            </SettingsSwitch>

            <SettingsSwitch
              testId="enable-sound-notifications-switch"
              name="enable-sound-notifications-switch"
              defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
            >
              {t(I18nKey.SETTINGS$SOUND_NOTIFICATIONS)}
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
          {t(I18nKey.BUTTON$RESET_TO_DEFAULTS)}
        </BrandButton>
        <BrandButton
          type="button"
          variant="primary"
          onClick={() => {
            formRef.current?.requestSubmit();
          }}
        >
          {t(I18nKey.BUTTON$SAVE)}
        </BrandButton>
      </footer>

      {resetSettingsModalIsOpen && (
        <ModalBackdrop>
          <div
            data-testid="reset-modal"
            className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary"
          >
            <p>{t(I18nKey.SETTINGS$RESET_CONFIRMATION)}</p>
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
