import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import React from "react";

interface ModelSelectorProps {
  models: Record<string, { separator: string; models: string[] }>;
  onModelChange: (model: string) => void;
}

export function ModelSelector({ models, onModelChange }: ModelSelectorProps) {
  const [litellmId, setLitellmId] = React.useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = React.useState<string | null>(
    null,
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

  return (
    <div>
      <span data-testid="model-id">{litellmId || "No model selected"}</span>

      <Autocomplete
        label="Provider"
        onSelectionChange={(e) => {
          if (e?.toString()) handleChangeProvider(e.toString());
        }}
      >
        {Object.keys(models).map((provider) => (
          <AutocompleteItem key={provider} value={provider}>
            {provider}
          </AutocompleteItem>
        ))}
      </Autocomplete>

      <Autocomplete
        label="Model"
        onSelectionChange={(e) => {
          if (e?.toString()) handleChangeModel(e.toString());
        }}
        isDisabled={!selectedProvider}
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
  );
}
