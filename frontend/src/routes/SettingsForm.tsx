import { Autocomplete, AutocompleteItem, Switch } from "@nextui-org/react";
import React from "react";
import { useFetcher } from "react-router-dom";
import { organizeModelsAndProviders } from "#/utils/organizeModelsAndProviders";
import { ModelSelector } from "#/components/modals/settings/ModelSelector";

interface SettingsFormProps {
  settings: {
    LLM_MODEL: string;
    AGENT: string;
  };
  models: string[];
  agents: string[];
}

export function SettingsForm({ settings, models, agents }: SettingsFormProps) {
  const fetcher = useFetcher();

  return (
    <fetcher.Form data-testid="settings-form" method="post" action="/settings">
      <Switch name="use-custom-model" data-testid="custom-model-toggle">
        Use custom model
      </Switch>

      <ModelSelector
        models={organizeModelsAndProviders(models)}
        defaultModel={settings.LLM_MODEL}
      />

      <fieldset data-testid="api-key-input">
        <label htmlFor="api-key">
          API Key
          <input id="api-key" name="api-key" type="password" />
        </label>
        <p>
          Don&apos;t know your API key? <span>Click here for instructions</span>
        </p>
      </fieldset>

      <fieldset data-testid="agent-selector">
        <label htmlFor="agent">
          Agent
          <Autocomplete
            id="agent"
            aria-label="Agent"
            data-testid="agent-input"
            name="agent"
            defaultSelectedKey={settings.AGENT}
          >
            {agents.map((agent) => (
              <AutocompleteItem key={agent} value={agent}>
                {agent}
              </AutocompleteItem>
            ))}
          </Autocomplete>
        </label>
      </fieldset>

      <div data-testid="security-analyzer-selector" />
      <div data-testid="confirmation-mode-toggle" />

      <button type="submit">Submit</button>
      <button type="button">Close</button>
      <button type="button">Reset to defaults</button>
    </fetcher.Form>
  );
}
