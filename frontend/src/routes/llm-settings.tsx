import React from "react";
import { useTranslation } from "react-i18next";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useSettings } from "#/hooks/query/use-settings";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { HelpLink } from "#/components/features/settings/help-link";
import { BrandButton } from "#/components/features/settings/brand-button";

function LlmSettingsScreen() {
  const { t } = useTranslation();
  const { mutate: saveSettings } = useSaveSettings();

  const { data: resources } = useAIConfigOptions();
  const { data: settings } = useSettings();

  const [view, setView] = React.useState<"basic" | "advanced">("basic");

  const [dirtyInputs, setDirtyInputs] = React.useState({
    model: false,
    apiKey: false,
    baseUrl: false,
    agent: false,
    confirmationMode: false,
    enableDefaultCondenser: false,
  });

  const modelsAndProviders = organizeModelsAndProviders(
    resources?.models || [],
  );

  React.useEffect(() => {
    const userSettingsIsAdvanced = hasAdvancedSettingsSet(settings || {});

    if (userSettingsIsAdvanced) setView("advanced");
    else setView("basic");
  }, [settings]);

  const basicFormAction = (formData: FormData) => {
    const provider = formData.get("llm-provider-input")?.toString();
    const model = formData.get("llm-model-input")?.toString();
    const apiKey = formData.get("llm-api-key-input")?.toString();

    const fullLlmModel =
      provider && model && `${provider}/${model}`.toLowerCase();

    saveSettings({
      LLM_MODEL: fullLlmModel,
      llm_api_key: apiKey,
    });
  };

  const advancedFormAction = (formData: FormData) => {
    const model = formData.get("llm-custom-model-input")?.toString();
    const baseUrl = formData.get("base-url-input")?.toString();
    const apiKey = formData.get("llm-api-key-input")?.toString();
    const agent = formData.get("agent-input")?.toString();
    const confirmationMode =
      formData.get("enable-confirmation-mode-switch")?.toString() === "on";
    const enableDefaultCondenser =
      formData.get("enable-memory-condenser-switch")?.toString() === "on";

    saveSettings({
      LLM_MODEL: model,
      LLM_BASE_URL: baseUrl,
      llm_api_key: apiKey,
      AGENT: agent,
      CONFIRMATION_MODE: confirmationMode,
      ENABLE_DEFAULT_CONDENSER: enableDefaultCondenser,
    });
  };

  const handleModelIsDirty = (model: string | null) => {
    // openai providers are special case; see ModelSelector
    // component for details
    const modelIsDirty = model !== settings?.LLM_MODEL.replace("openai/", "");
    setDirtyInputs((prev) => ({
      ...prev,
      model: modelIsDirty,
    }));
  };

  const handleApiKeyIsDirty = (apiKey: string) => {
    const apiKeyIsDirty = apiKey !== "";
    setDirtyInputs((prev) => ({
      ...prev,
      apiKey: apiKeyIsDirty,
    }));
  };

  const handleCustomModelIsDirty = (model: string) => {
    const modelIsDirty = model !== settings?.LLM_MODEL && model !== "";
    setDirtyInputs((prev) => ({
      ...prev,
      model: modelIsDirty,
    }));
  };

  const handleBaseUrlIsDirty = (baseUrl: string) => {
    const baseUrlIsDirty = baseUrl !== settings?.LLM_BASE_URL;
    setDirtyInputs((prev) => ({
      ...prev,
      baseUrl: baseUrlIsDirty,
    }));
  };

  const handleAgentIsDirty = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newAgent = e.target.value;
    const agentIsDirty = newAgent !== settings?.AGENT && newAgent !== "";
    setDirtyInputs((prev) => ({
      ...prev,
      agent: agentIsDirty,
    }));
  };

  const handleConfirmationModeIsDirty = (isToggled: boolean) => {
    const confirmationModeIsDirty = isToggled !== settings?.CONFIRMATION_MODE;
    setDirtyInputs((prev) => ({
      ...prev,
      confirmationMode: confirmationModeIsDirty,
    }));
  };

  const handleEnableDefaultCondenserIsDirty = (isToggled: boolean) => {
    const enableDefaultCondenserIsDirty =
      isToggled !== settings?.ENABLE_DEFAULT_CONDENSER;
    setDirtyInputs((prev) => ({
      ...prev,
      enableDefaultCondenser: enableDefaultCondenserIsDirty,
    }));
  };

  const formIsDirty = Object.values(dirtyInputs).some((isDirty) => isDirty);

  if (!settings) return null;

  return (
    <div
      data-testid="llm-settings-screen"
      className="flex flex-col gap-6 px-11 py-9"
    >
      <SettingsSwitch
        testId="advanced-settings-switch"
        defaultIsToggled={view === "advanced"}
        onToggle={(isToggled) => {
          setView(isToggled ? "advanced" : "basic");
        }}
      >
        {t(I18nKey.SETTINGS$ADVANCED)}
      </SettingsSwitch>

      <form action={view === "basic" ? basicFormAction : advancedFormAction}>
        {view === "basic" && (
          <div
            data-testid="llm-settings-form-basic"
            className="flex flex-col gap-6"
          >
            <ModelSelector
              models={modelsAndProviders}
              currentModel={
                settings.LLM_MODEL || "anthropic/claude-3-5-sonnet-20241022"
              }
              onChange={handleModelIsDirty}
            />

            <SettingsInput
              testId="llm-api-key-input"
              name="llm-api-key-input"
              label={t(I18nKey.SETTINGS_FORM$API_KEY)}
              type="password"
              className="w-[680px]"
              placeholder={settings.LLM_API_KEY_SET ? "<hidden>" : ""}
              onChange={handleApiKeyIsDirty}
            />

            <HelpLink
              testId="llm-api-key-help-anchor"
              text={t(I18nKey.SETTINGS$DONT_KNOW_API_KEY)}
              linkText={t(I18nKey.SETTINGS$CLICK_FOR_INSTRUCTIONS)}
              href="https://docs.all-hands.dev/modules/usage/installation#getting-an-api-key"
            />
          </div>
        )}

        {view === "advanced" && (
          <div
            data-testid="llm-settings-form-advanced"
            className="flex flex-col gap-6"
          >
            <SettingsInput
              testId="llm-custom-model-input"
              name="llm-custom-model-input"
              label={t(I18nKey.SETTINGS$CUSTOM_MODEL)}
              defaultValue={
                settings.LLM_MODEL || "anthropic/claude-3-5-sonnet-20241022"
              }
              placeholder="anthropic/claude-3-5-sonnet-20241022"
              type="text"
              className="w-[680px]"
              onChange={handleCustomModelIsDirty}
            />

            <SettingsInput
              testId="base-url-input"
              name="base-url-input"
              label={t(I18nKey.SETTINGS$BASE_URL)}
              defaultValue={settings.LLM_BASE_URL}
              placeholder="https://api.openai.com"
              type="text"
              className="w-[680px]"
              onChange={handleBaseUrlIsDirty}
            />

            <SettingsInput
              testId="llm-api-key-input"
              name="llm-api-key-input"
              label={t(I18nKey.SETTINGS_FORM$API_KEY)}
              type="password"
              className="w-[680px]"
              placeholder={settings.LLM_API_KEY_SET ? "<hidden>" : ""}
              onChange={handleApiKeyIsDirty}
            />
            <HelpLink
              testId="llm-api-key-help-anchor"
              text={t(I18nKey.SETTINGS$DONT_KNOW_API_KEY)}
              linkText={t(I18nKey.SETTINGS$CLICK_FOR_INSTRUCTIONS)}
              href="https://docs.all-hands.dev/modules/usage/installation#getting-an-api-key"
            />
            <input
              data-testid="agent-input"
              name="agent-input"
              defaultValue={settings.AGENT}
              onChange={handleAgentIsDirty}
            />
            <SettingsSwitch
              testId="enable-confirmation-mode-switch"
              name="enable-confirmation-mode-switch"
              onToggle={handleConfirmationModeIsDirty}
              defaultIsToggled={settings.CONFIRMATION_MODE}
              isBeta
            >
              {t(I18nKey.SETTINGS$CONFIRMATION_MODE)}
            </SettingsSwitch>

            <SettingsSwitch
              testId="enable-memory-condenser-switch"
              name="enable-memory-condenser-switch"
              defaultIsToggled={settings.ENABLE_DEFAULT_CONDENSER}
              onToggle={handleEnableDefaultCondenserIsDirty}
            >
              {t(I18nKey.SETTINGS$ENABLE_MEMORY_CONDENSATION)}
            </SettingsSwitch>
          </div>
        )}

        <BrandButton
          testId="submit-button"
          type="submit"
          variant="primary"
          isDisabled={!formIsDirty}
        >
          Save Changes
        </BrandButton>
      </form>
    </div>
  );
}

export default LlmSettingsScreen;
