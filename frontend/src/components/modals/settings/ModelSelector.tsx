import React from "react";

interface ModelSelectorProps {
  models: Record<string, { separator: string; models: string[] }>;
}

export function ModelSelector({ models }: ModelSelectorProps) {
  const [litellmId, setLitellmId] = React.useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = React.useState<string | null>(
    null,
  );

  const onChangeProvider = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const provider = e.target.value;
    setSelectedProvider(provider);

    const separator = models[provider]?.separator || "";
    setLitellmId(provider + separator);
  };

  const onChangeModel = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const model = e.target.value;
    setLitellmId((prev) => prev + model);
  };

  return (
    <div>
      <span data-testid="model-id">{litellmId || "No model selected"}</span>

      <label>
        Provider
        <select id="provider" onChange={onChangeProvider}>
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
          onChange={onChangeModel}
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
