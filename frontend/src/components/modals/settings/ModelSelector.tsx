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

  const handleChangeProvider = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const provider = e.target.value;
    setSelectedProvider(provider);

    const separator = models[provider]?.separator || "";
    setLitellmId(provider + separator);
  };

  const handleChangeModel = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const separator = models[selectedProvider || ""]?.separator || "";
    const model = selectedProvider + separator + e.target.value;
    setLitellmId(model);
    onModelChange(model);
  };

  return (
    <div>
      <span data-testid="model-id">{litellmId || "No model selected"}</span>

      <label>
        Provider
        <select id="provider" onChange={handleChangeProvider}>
          <option value="">Select a provider</option>
          {Object.keys(models).map((provider) => (
            <option key={provider} value={provider}>
              {provider}
            </option>
          ))}
        </select>
      </label>

      <label>
        Model
        <select
          id="model"
          onChange={handleChangeModel}
          disabled={!selectedProvider}
        >
          <option value="">Select a model</option>
          {selectedProvider &&
            models[selectedProvider].models.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
        </select>
      </label>
    </div>
  );
}
