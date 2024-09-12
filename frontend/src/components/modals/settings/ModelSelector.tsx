import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
} from "@nextui-org/react";
import React from "react";
import { mapProvider } from "#/utils/mapProvider";
import { VERIFIED_MODELS, VERIFIED_PROVIDERS } from "#/utils/verified-models";
import { extractModelAndProvider } from "#/utils/extractModelAndProvider";

interface ModelSelectorProps {
  isDisabled?: boolean;
  models: Record<string, { separator: string; models: string[] }>;
  onModelChange: (model: string) => void;
  defaultModel?: string;
}

export function ModelSelector({
  isDisabled,
  models,
  onModelChange,
  defaultModel,
}: ModelSelectorProps) {
  const [, setLitellmId] = React.useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = React.useState<string | null>(
    null,
  );
  const [selectedModel, setSelectedModel] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (defaultModel) {
      // runs when resetting to defaults
      const { provider, model } = extractModelAndProvider(defaultModel);

      setLitellmId(defaultModel);
      setSelectedProvider(provider);
      setSelectedModel(model);
    }
  }, [defaultModel]);

  const handleChangeProvider = (provider: string) => {
    setSelectedProvider(provider);
    setSelectedModel(null);

    const separator = models[provider]?.separator || "";
    setLitellmId(provider + separator);
  };

  const handleChangeModel = (model: string) => {
    const separator = models[selectedProvider || ""]?.separator || "";
    let fullModel = selectedProvider + separator + model;
    if (selectedProvider === "openai") {
      // LiteLLM lists OpenAI models without the openai/ prefix
      fullModel = model;
    }
    setLitellmId(fullModel);
    onModelChange(fullModel);
    setSelectedModel(model);
  };

  const clear = () => {
    setSelectedProvider(null);
    setLitellmId(null);
  };

  return (
    <div data-testid="model-selector" className="flex flex-col gap-2">
      <div className="flex flex-row gap-3">
        <Autocomplete
          isDisabled={isDisabled}
          label="LLM Provider"
          placeholder="Select a provider"
          isClearable={false}
          onSelectionChange={(e) => {
            if (e?.toString()) handleChangeProvider(e.toString());
          }}
          onInputChange={(value) => !value && clear()}
          defaultSelectedKey={selectedProvider ?? undefined}
          selectedKey={selectedProvider}
        >
          <AutocompleteSection title="Verified">
            {Object.keys(models)
              .filter((provider) => VERIFIED_PROVIDERS.includes(provider))
              .map((provider) => (
                <AutocompleteItem key={provider} value={provider}>
                  {mapProvider(provider)}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
          <AutocompleteSection title="Others">
            {Object.keys(models)
              .filter((provider) => !VERIFIED_PROVIDERS.includes(provider))
              .map((provider) => (
                <AutocompleteItem key={provider} value={provider}>
                  {mapProvider(provider)}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
        </Autocomplete>

        <Autocomplete
          label="LLM Model"
          placeholder="Select a model"
          onSelectionChange={(e) => {
            if (e?.toString()) handleChangeModel(e.toString());
          }}
          isDisabled={isDisabled || !selectedProvider}
          selectedKey={selectedModel}
          defaultSelectedKey={selectedModel ?? undefined}
        >
          <AutocompleteSection title="Verified">
            {models[selectedProvider || ""]?.models
              .filter((model) => VERIFIED_MODELS.includes(model))
              .map((model) => (
                <AutocompleteItem key={model} value={model}>
                  {model}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
          <AutocompleteSection title="Others">
            {models[selectedProvider || ""]?.models
              .filter((model) => !VERIFIED_MODELS.includes(model))
              .map((model) => (
                <AutocompleteItem key={model} value={model}>
                  {model}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
        </Autocomplete>
      </div>
    </div>
  );
}
