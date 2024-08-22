import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
} from "@nextui-org/react";
import React from "react";
import { mapProvider } from "#/utils/mapProvider";
import { VERIFIED_PROVIDERS } from "#/utils/verified-models";
import { extractModelAndProvider } from "#/utils/extractModelAndProvider";

interface ModelSelectorProps {
  isDisabled?: boolean;
  models: Record<string, { separator: string; models: string[] }>;
  onModelChange: (model: string) => void;
  defaultValue?: string;
}

export function ModelSelector({
  isDisabled,
  models,
  onModelChange,
  defaultValue,
}: ModelSelectorProps) {
  const [litellmId, setLitellmId] = React.useState<string | null>(
    defaultValue ?? null,
  );
  const [selectedProvider, setSelectedProvider] = React.useState<string | null>(
    extractModelAndProvider(defaultValue ?? "")?.provider ?? null,
  );

  const handleChangeProvider = (provider: string) => {
    setSelectedProvider(provider);

    const separator = models[provider]?.separator || "";
    setLitellmId(provider + separator);
  };

  const handleChangeModel = (model: string) => {
    const separator = models[selectedProvider || ""]?.separator || "";
    const fullModel = selectedProvider + separator + model;
    setLitellmId(fullModel);
    onModelChange(fullModel);
  };

  const clear = () => {
    setSelectedProvider(null);
    setLitellmId(null);
  };

  return (
    <div className="flex flex-col gap-2">
      <span className="text-center italic text-gray-500" data-testid="model-id">
        {litellmId?.replace("other", "") || "No model selected"}
      </span>

      <div className="flex flex-col gap-3">
        <Autocomplete
          isDisabled={isDisabled}
          label="Provider"
          placeholder="Select a provider"
          isClearable={false}
          onSelectionChange={(e) => {
            if (e?.toString()) handleChangeProvider(e.toString());
          }}
          onInputChange={(value) => !value && clear()}
          defaultSelectedKey={selectedProvider ?? undefined}
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
          label="Model"
          placeholder="Select a model"
          onSelectionChange={(e) => {
            if (e?.toString()) handleChangeModel(e.toString());
          }}
          isDisabled={isDisabled || !selectedProvider}
          defaultSelectedKey={
            extractModelAndProvider(defaultValue ?? "")?.model ?? undefined
          }
        >
          {selectedProvider ? (
            models[selectedProvider].models.map((model) => (
              <AutocompleteItem key={model} value={model}>
                {model}
              </AutocompleteItem>
            ))
          ) : (
            <AutocompleteItem key="" value="">
              Select a model
            </AutocompleteItem>
          )}
        </Autocomplete>
      </div>
    </div>
  );
}
