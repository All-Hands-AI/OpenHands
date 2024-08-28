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
  currentModel?: string;
}

export function ModelSelector({
  isDisabled,
  models,
  currentModel,
}: ModelSelectorProps) {
  const [litellmId, setLitellmId] = React.useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = React.useState<string | null>(
    null,
  );
  const [selectedModel, setSelectedModel] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (currentModel) {
      // runs when resetting to defaults
      const { provider, model } = extractModelAndProvider(currentModel);

      setLitellmId(currentModel);
      setSelectedProvider(provider);
      setSelectedModel(model);
    }
  }, [currentModel]);

  const handleChangeProvider = (provider: string) => {
    setSelectedProvider(provider);
    setSelectedModel(null);

    const separator = models[provider]?.separator || "";
    setLitellmId(provider + separator);
  };

  const handleChangeModel = (model: string) => {
    const separator = models[selectedProvider || ""]?.separator || "";
    const fullModel = selectedProvider + separator + model;
    setLitellmId(fullModel);
    setSelectedModel(model);
  };

  const clear = () => {
    setSelectedProvider(null);
    setLitellmId(null);
  };

  return (
    <div data-testid="model-selector" className="flex flex-col gap-2">
      <span
        className="text-center italic text-[#A3A3A3] text-sm"
        data-testid="model-id"
      >
        {litellmId?.replace("other", "") || "No model selected"}
      </span>

      <input
        type="text"
        hidden
        aria-hidden
        name="model"
        defaultValue={litellmId || ""}
      />

      <div className="flex flex-col gap-3">
        <fieldset className="flex flex-col gap-2">
          <label
            htmlFor="provider"
            className="font-[500] text-[#A3A3A3] text-xs"
          >
            Provider
          </label>
          <Autocomplete
            id="provider"
            isDisabled={isDisabled}
            aria-label="Provider"
            placeholder="Select a provider"
            isClearable={false}
            onSelectionChange={(e) => {
              if (e?.toString()) handleChangeProvider(e.toString());
            }}
            onInputChange={(value) => !value && clear()}
            defaultSelectedKey={selectedProvider ?? undefined}
            selectedKey={selectedProvider}
            inputProps={{
              classNames: {
                inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
              },
            }}
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
        </fieldset>

        <fieldset className="flex flex-col gap-2">
          <label htmlFor="model" className="font-[500] text-[#A3A3A3] text-xs">
            Model
          </label>
          <Autocomplete
            id="model"
            aria-label="Model"
            placeholder="Select a model"
            onSelectionChange={(e) => {
              if (e?.toString()) handleChangeModel(e.toString());
            }}
            isDisabled={isDisabled || !selectedProvider}
            selectedKey={selectedModel}
            defaultSelectedKey={selectedModel ?? undefined}
            inputProps={{
              classNames: {
                inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
              },
            }}
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
        </fieldset>
      </div>
    </div>
  );
}
