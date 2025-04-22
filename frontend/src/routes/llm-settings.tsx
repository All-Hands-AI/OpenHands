import React from "react";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useSettings } from "#/hooks/query/use-settings";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";

function LlmSettingsScreen() {
  const { mutate: saveSettings } = useSaveSettings();

  const { data: resources } = useAIConfigOptions();
  const { data: settings } = useSettings();

  const [view, setView] = React.useState<"basic" | "advanced">("basic");

  const modelsAndProviders = organizeModelsAndProviders(
    resources?.models || [],
  );

  React.useEffect(() => {
    const userSettingsIsAdvanced = hasAdvancedSettingsSet(settings || {});

    if (userSettingsIsAdvanced) setView("advanced");
    else setView("basic");
  }, [settings]);

  if (!settings) return null;

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

  return (
    <div data-testid="llm-settings-screen">
      <input
        type="checkbox"
        data-testid="advanced-settings-switch"
        checked={view === "advanced"}
        onChange={(e) => setView(e.target.checked ? "advanced" : "basic")}
      />

      <form action={view === "basic" ? basicFormAction : advancedFormAction}>
        {view === "basic" && (
          <div data-testid="llm-settings-form-basic">
            <ModelSelector
              models={modelsAndProviders}
              currentModel={
                settings.LLM_MODEL || "anthropic/claude-3-5-sonnet-20241022"
              }
            />

            <input
              data-testid="llm-api-key-input"
              name="llm-api-key-input"
              defaultValue=""
              placeholder={settings.LLM_API_KEY_SET ? "<hidden>" : ""}
            />
            <div data-testid="llm-api-key-help-anchor" />
          </div>
        )}

        {view === "advanced" && (
          <div data-testid="llm-settings-form-advanced">
            <input
              data-testid="llm-custom-model-input"
              name="llm-custom-model-input"
              defaultValue={
                settings.LLM_MODEL || "anthropic/claude-3-5-sonnet-20241022"
              }
            />
            <input
              data-testid="base-url-input"
              name="base-url-input"
              defaultValue={settings.LLM_BASE_URL}
            />
            <input
              data-testid="llm-api-key-input"
              name="llm-api-key-input"
              defaultValue=""
              placeholder={settings.LLM_API_KEY_SET ? "<hidden>" : ""}
            />
            <div data-testid="llm-api-key-help-anchor" />
            <input
              data-testid="agent-input"
              name="agent-input"
              defaultValue={settings.AGENT}
            />
            <input
              type="checkbox"
              data-testid="enable-confirmation-mode-switch"
              name="enable-confirmation-mode-switch"
              defaultChecked={settings.CONFIRMATION_MODE}
            />
            <input
              type="checkbox"
              data-testid="enable-memory-condenser-switch"
              name="enable-memory-condenser-switch"
              defaultChecked={settings.ENABLE_DEFAULT_CONDENSER}
            />
          </div>
        )}

        <button data-testid="submit-button" type="submit">
          Save Changes
        </button>
      </form>
    </div>
  );
}

export default LlmSettingsScreen;
