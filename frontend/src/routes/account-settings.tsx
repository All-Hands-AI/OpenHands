import React from "react";
import { Link } from "react-router";
import { cn } from "@heroui/react";
import PlusIcon from "#/icons/plus.svg?react";
import CloseIcon from "#/icons/close.svg?react";
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
import { PostSettings, ProviderOptions } from "#/types/settings";
import { useAuth } from "#/context/auth-context";

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
  const [secrets, setSecrets] = React.useState(
    Object.entries(settings?.CUSTOM_SECRETS || {}),
  );

  const [secretsToDelete, setSecretsToDelete] = React.useState<number[]>([]);

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

  React.useEffect(() => {
    setSecrets(Object.entries(settings?.CUSTOM_SECRETS || {}));
    setSecretsToDelete([]);
  }, [settings?.CUSTOM_SECRETS]);

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
      (isLLMKeySet
        ? undefined // don't update if it's already set
        : ""); // reset if it's first time save to avoid 500 error

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

    const secretsEntries: Record<string, string> = {};

    secrets.forEach((_, index) => {
      const name = formData.get(`secret-name-${index}`)?.toString().trim();
      const value = formData.get(`secret-value-${index}`)?.toString();

      if (name && !secretsToDelete.includes(index)) {
        secretsEntries[name] = value || "";
      }
    });

    const newSettings = {
      provider_tokens:
        githubToken || gitlabToken
          ? {
              github: githubToken || "",
              gitlab: gitlabToken || "",
            }
          : undefined,
      custom_secrets: secretsEntries,
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
    const newSettings: Partial<PostSettings> = {
      ...DEFAULT_SETTINGS,
      LLM_API_KEY: "", // reset LLM API key
      provider_tokens: {
        github: "",
        gitlab: "",
      },
      custom_secrets: {},
    };

    // we don't want the user to be able to modify these settings in SaaS
    // and we should make sure they aren't included in the reset
    if (shouldHandleSpecialSaasCase) {
      delete newSettings.LLM_API_KEY;
      delete newSettings.LLM_BASE_URL;
      delete newSettings.LLM_MODEL;
    }

    saveSettings(newSettings, {
      onSuccess: () => {
        displaySuccessToast("Settings reset");
        setResetSettingsModalIsOpen(false);
        setLlmConfigMode(isAdvancedSettingsSet ? "advanced" : "basic");
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

  const handleAddSecret = () => {
    setSecrets([...secrets, ["", ""]]);
  };

  const markSecretDeletion = (index: number, isSecretMarked: boolean) => {
    if (isSecretMarked) {
      setSecretsToDelete(secretsToDelete.filter((item) => item !== index));
    } else setSecretsToDelete([...secretsToDelete, index]);
  };

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
                  LLM Settings
                </h2>
                {!shouldHandleSpecialSaasCase && (
                  <SettingsSwitch
                    testId="advanced-settings-switch"
                    defaultIsToggled={isAdvancedSettingsSet}
                    onToggle={onToggleAdvancedMode}
                  >
                    Advanced
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
                  label="Custom Model"
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
                  label="Base URL"
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
                  label="API Key"
                  type="password"
                  className="w-[680px]"
                  startContent={
                    isLLMKeySet && <KeyStatusIcon isSet={isLLMKeySet} />
                  }
                  placeholder={isLLMKeySet ? "**********" : ""}
                />
              )}

              {!shouldHandleSpecialSaasCase && (
                <HelpLink
                  testId="llm-api-key-help-anchor"
                  text="Don't know your API key?"
                  linkText="Click here for instructions"
                  href="https://docs.all-hands.dev/modules/usage/llms"
                />
              )}

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
                  label={
                    <>
                      Runtime Settings (
                      <a href="mailto:contact@all-hands.dev">
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

              {llmConfigMode === "advanced" && (
                <SettingsSwitch
                  testId="enable-memory-condenser-switch"
                  name="enable-memory-condenser-switch"
                  defaultIsToggled={!!settings.ENABLE_DEFAULT_CONDENSER}
                >
                  Enable memory condensation
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
          )}

          <section className="flex flex-col gap-6">
            <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
              Git Provider Settings
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

                <p data-testId="github-token-help-anchor" className="text-xs">
                  {" "}
                  Generate a token on{" "}
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
                  or see the{" "}
                  <b>
                    <a
                      href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
                      target="_blank"
                      className="underline underline-offset-2"
                      rel="noopener noreferrer"
                    >
                      documentation
                    </a>
                  </b>
                  .
                </p>

                <SettingsInput
                  testId="gitlab-token-input"
                  name="gitlab-token-input"
                  label="GitLab Token"
                  type="password"
                  className="w-[680px]"
                  startContent={
                    isGitLabTokenSet && (
                      <KeyStatusIcon isSet={!!isGitLabTokenSet} />
                    )
                  }
                  placeholder={isGitLabTokenSet ? "**********" : ""}
                />

                <p data-testId="gitlab-token-help-anchor" className="text-xs">
                  {" "}
                  Generate a token on{" "}
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
                  or see the{" "}
                  <b>
                    <a
                      href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
                      target="_blank"
                      className="underline underline-offset-2"
                      rel="noopener noreferrer"
                    >
                      documentation
                    </a>
                  </b>
                  .
                </p>
              </>
            )}

            <BrandButton
              type="button"
              variant="secondary"
              onClick={handleLogout}
              isDisabled={!providersAreSet}
            >
              Disconnect Tokens
            </BrandButton>
          </section>

          <section className="flex flex-col gap-6">
            <div className="flex justify-between items-center">
              <h2 className="text-[28px] font-bold">Custom Secrets</h2>
              <button
                type="button"
                onClick={handleAddSecret}
                className="p-2 text-primary hover:text-primary/80"
              >
                <PlusIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="flex flex-col gap-4">
              {secrets.map(([secretName, secretValue], index) => {
                const isMarkedForDeletion = secretsToDelete.includes(index);

                return (
                  <div
                    key={`${secretName}-${index}`}
                    className={cn(
                      "flex items-end gap-2",
                      isMarkedForDeletion && "opacity-50",
                    )}
                  >
                    <SettingsInput
                      name={`secret-name-${index}`}
                      placeholder="Secret Name"
                      defaultValue={secretName}
                      className="w-[330px]"
                      label="Secret Name"
                      type="text"
                      isDisabled={isMarkedForDeletion}
                    />
                    <SettingsInput
                      name={`secret-value-${index}`}
                      type="password"
                      placeholder={
                        Object.keys(settings?.CUSTOM_SECRETS || {}).includes(
                          secretName,
                        )
                          ? "**********"
                          : ""
                      }
                      defaultValue={secretValue}
                      className="w-[330px]"
                      label="Secret Value"
                      isDisabled={isMarkedForDeletion}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        markSecretDeletion(index, isMarkedForDeletion)
                      }
                      className="flex items-center justify-center h-10 p-1 text-gray-400 hover:text-gray-300"
                    >
                      {isMarkedForDeletion ? (
                        <span className="text-xs text-blue-400 hover:underline">
                          Undo
                        </span>
                      ) : (
                        <CloseIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                );
              })}
              {secretsToDelete.length > 0 && (
                <p className="text-xs text-red-400 italic">
                  Disabled secrets will be deleted when you save changes.
                </p>
              )}
            </div>
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

            <SettingsSwitch
              testId="enable-sound-notifications-switch"
              name="enable-sound-notifications-switch"
              defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
            >
              Enable sound notifications
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
            className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary"
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
