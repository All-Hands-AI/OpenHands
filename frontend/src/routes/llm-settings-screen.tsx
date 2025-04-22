import React from "react";

function LlmSettingsScreen() {
  const [view, setView] = React.useState<"basic" | "advanced">("basic");

  return (
    <div>
      <input
        type="checkbox"
        data-testid="advanced-settings-switch"
        onChange={(e) => setView(e.target.checked ? "advanced" : "basic")}
      />

      {view === "basic" && (
        <div data-testid="llm-settings-form-basic">
          <div data-testid="llm-provider-input" />
          <div data-testid="llm-model-input" />
          <div data-testid="llm-api-key-input" />
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
