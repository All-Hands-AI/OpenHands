import React from "react";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useSettings } from "#/hooks/query/use-settings";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";

function LlmSettingsScreen() {
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

  return (
    <div data-testid="llm-settings-screen">
      <input
        type="checkbox"
        data-testid="advanced-settings-switch"
        checked={view === "advanced"}
        onChange={(e) => setView(e.target.checked ? "advanced" : "basic")}
      />

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
            defaultValue={
              settings.LLM_MODEL || "anthropic/claude-3-5-sonnet-20241022"
            }
          />
          <input
            data-testid="base-url-input"
            defaultValue={settings.LLM_BASE_URL}
          />
          <input
            data-testid="llm-api-key-input"
            defaultValue=""
            placeholder={settings.LLM_API_KEY_SET ? "<hidden>" : ""}
          />
          <div data-testid="llm-api-key-help-anchor" />
          <input data-testid="agent-input" defaultValue={settings.AGENT} />
          <input
            type="checkbox"
            data-testid="enable-confirmation-mode-switch"
            defaultChecked={settings.CONFIRMATION_MODE}
          />
          <input
            type="checkbox"
            data-testid="enable-memory-condenser-switch"
            defaultChecked={settings.ENABLE_DEFAULT_CONDENSER}
          />
        </div>
      )}
    </div>
  );
}

export default LlmSettingsScreen;
