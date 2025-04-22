import React from "react";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useSettings } from "#/hooks/query/use-settings";

function LlmSettingsScreen() {
  const { data: resources } = useAIConfigOptions();
  const { data: settings } = useSettings();

  const [view, setView] = React.useState<"basic" | "advanced">("basic");

  const modelsAndProviders = organizeModelsAndProviders(
    resources?.models || [],
  );

  return (
    <div>
      <input
        type="checkbox"
        data-testid="advanced-settings-switch"
        onChange={(e) => setView(e.target.checked ? "advanced" : "basic")}
      />

      {view === "basic" && (
        <div data-testid="llm-settings-form-basic">
          <ModelSelector
            models={modelsAndProviders}
            currentModel={
              settings?.LLM_MODEL || "anthropic/claude-3-5-sonnet-20241022"
            }
          />

          <input
            data-testid="llm-api-key-input"
            defaultValue=""
            placeholder={settings?.LLM_API_KEY_SET ? "<hidden>" : ""}
          />
          <div data-testid="llm-api-key-help-anchor" />
        </div>
      )}

      {view === "advanced" && (
        <div data-testid="llm-settings-form-advanced">
          <div data-testid="llm-custom-model-input" />
          <div data-testid="base-url-input" />
          <div data-testid="llm-api-key-input" />
          <div data-testid="llm-api-key-help-anchor" />
          <div data-testid="agent-input" />
          <div data-testid="enable-confirmation-mode-switch" />
          <div data-testid="enable-memory-condenser-switch" />
        </div>
      )}
    </div>
  );
}

export default LlmSettingsScreen;
