import React from "react";
import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { useAppLogout } from "#/hooks/use-app-logout";
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
import { LlmCustomModelInput } from "#/components/features/settings/account/llm-custom-model-input";
import { BaseUrlInput } from "#/components/features/settings/account/base-url-input";
import { AgentInput } from "#/components/features/settings/account/agent-input";
import { RuntimeSettingsInput } from "#/components/features/settings/account/runtime-settings-input";
import { EnableConfirmationModeSwitch } from "#/components/features/settings/account/enable-confirmation-mode-switch";
import { EnableMemoryCondensorSwitch } from "#/components/features/settings/account/enable-memory-condensor-switch";
import { SecurityAnalzerInput } from "#/components/features/settings/account/security-analyzer-input";
import { EnableAnalyticsSwitch } from "#/components/features/settings/account/enable-analytics-switch";
import { EnableSoundNotificationsSwitch } from "#/components/features/settings/account/enable-sound-notification-switch";
import { LanguageInput } from "#/components/features/settings/account/language-input";
import { buildUserPreferences } from "#/utils/build-user-preferences";
import {
  GitHubTokenInput,
  GitLabTokenInput,
} from "#/components/features/settings/account/git-provider-token-input";
import { ConfirmResetSettingsModal } from "#/components/features/settings/account/confirm-reset-settings-modal";
import { AdvancedSettingsSwitch } from "#/components/features/settings/account/advanced-settings-switch";
import { LlmApiKeyInput } from "#/components/features/settings/account/llm-api-key-input";

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

  /**
   * Submits the user's preferences to the server.
   */
  const onSubmit = async (formData: FormData) => {
    const newSettings = buildUserPreferences(
      formData,
      isLLMKeySet,
      shouldHandleSpecialSaasCase,
      confirmationModeIsEnabled,
    );

    saveSettings(newSettings, {
      onSuccess: () => {
        handleCaptureConsent(newSettings.user_consents_to_analytics);
        displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
        setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
      },
      onError: (error) => {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
      },
    });
  };

  /**
   * Resets the user's settings to the default values.
   */
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
                  <AdvancedSettingsSwitch
                    defaultIsToggled={isAdvancedSettingsSet}
                    onToggle={onToggleAdvancedMode}
                  />
                )}
              </div>

              {llmConfigMode === "basic" && !shouldHandleSpecialSaasCase && (
                <ModelSelector
                  models={modelsAndProviders}
                  currentModel={settings.LLM_MODEL}
                />
              )}

              {llmConfigMode === "advanced" && !shouldHandleSpecialSaasCase && (
                <LlmCustomModelInput defaultModel={settings.LLM_MODEL} />
              )}

              {llmConfigMode === "advanced" && !shouldHandleSpecialSaasCase && (
                <BaseUrlInput defaultBaseUrl={settings.LLM_BASE_URL} />
              )}

              {!shouldHandleSpecialSaasCase && (
                <LlmApiKeyInput isLLMKeySet={!!isLLMKeySet} />
              )}

              {llmConfigMode === "advanced" && (
                <AgentInput
                  agents={resources?.agents || []}
                  defaultAgent={settings.AGENT}
                />
              )}

              {isSaas && llmConfigMode === "advanced" && (
                <RuntimeSettingsInput
                  defaultRuntime={settings.REMOTE_RUNTIME_RESOURCE_FACTOR?.toString()}
                />
              )}

              {llmConfigMode === "advanced" && (
                <EnableConfirmationModeSwitch
                  onToggle={setConfirmationModeIsEnabled}
                  defaultIsToggled={!!settings.CONFIRMATION_MODE}
                />
              )}

              {llmConfigMode === "advanced" && (
                <EnableMemoryCondensorSwitch
                  defaultIsToggled={!!settings.ENABLE_DEFAULT_CONDENSER}
                />
              )}

              {llmConfigMode === "advanced" && confirmationModeIsEnabled && (
                <SecurityAnalzerInput
                  securityAnalyzers={resources?.securityAnalyzers || []}
                  defaultSecurityAnalyzer={settings.SECURITY_ANALYZER}
                />
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
                <GitHubTokenInput isGitHubTokenSet={isGitHubTokenSet} />
                <GitLabTokenInput isGitLabTokenSet={isGitLabTokenSet} />

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

            <LanguageInput defaultLanguage={settings.LANGUAGE} />
            <EnableAnalyticsSwitch defaultIsToggled={!!isAnalyticsEnabled} />
            <EnableSoundNotificationsSwitch
              defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
            />
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
        <ConfirmResetSettingsModal
          handleReset={handleReset}
          onClose={() => setResetSettingsModalIsOpen(false)}
        />
      )}
    </>
  );
}

export default AccountSettings;
