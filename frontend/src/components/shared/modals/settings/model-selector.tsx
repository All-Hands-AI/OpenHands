import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
} from "@heroui/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { mapProvider } from "#/utils/map-provider";
import { VERIFIED_MODELS, VERIFIED_PROVIDERS } from "#/utils/verified-models";
import { extractModelAndProvider } from "#/utils/extract-model-and-provider";

interface ModelSelectorProps {
  isDisabled?: boolean;
  models: Record<string, { separator: string; models: string[] }>;
  currentModel?: string;
  onChange?: (model: string | null) => void;
}

export function ModelSelector({
  isDisabled,
  models,
  currentModel,
  onChange,
}: ModelSelectorProps) {
  const [, setLitellmId] = React.useState<string | null>(null);
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
    let fullModel = selectedProvider + separator + model;
    if (selectedProvider === "openai") {
      // LiteLLM lists OpenAI models without the openai/ prefix
      fullModel = model;
    }
    setLitellmId(fullModel);
    setSelectedModel(model);
    onChange?.(fullModel);
  };

  const clear = () => {
    setSelectedProvider(null);
    setLitellmId(null);
  };

  const { t } = useTranslation();

  return (
    <div className="flex flex-col md:flex-row w-[full] md:w-[680px] justify-between gap-4 md:gap-[46px]">
      <fieldset className="flex flex-col gap-2.5 w-full">
        <label className="text-sm">{t(I18nKey.LLM$PROVIDER)}</label>
        <Autocomplete
          data-testid="llm-provider-input"
          isRequired
          isVirtualized={false}
          name="llm-provider-input"
          isDisabled={isDisabled}
          aria-label={t(I18nKey.LLM$PROVIDER)}
          placeholder={t(I18nKey.LLM$SELECT_PROVIDER_PLACEHOLDER)}
          isClearable={false}
          onSelectionChange={(e) => {
            if (e?.toString()) handleChangeProvider(e.toString());
          }}
          onInputChange={(value) => !value && clear()}
          defaultSelectedKey={selectedProvider ?? undefined}
          selectedKey={selectedProvider}
          classNames={{
            popoverContent: "bg-tertiary rounded-xl border border-[#717888]",
          }}
          inputProps={{
            classNames: {
              inputWrapper:
                "bg-tertiary border border-[#717888] h-10 w-full rounded-sm p-2 placeholder:italic",
            },
          }}
        >
          <AutocompleteSection title={t(I18nKey.MODEL_SELECTOR$VERIFIED)}>
            {Object.keys(models)
              .filter((provider) => VERIFIED_PROVIDERS.includes(provider))
              .map((provider) => (
                <AutocompleteItem
                  data-testid={`provider-item-${provider}`}
                  key={provider}
                >
                  {mapProvider(provider)}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
          <AutocompleteSection title={t(I18nKey.MODEL_SELECTOR$OTHERS)}>
            {Object.keys(models)
              .filter((provider) => !VERIFIED_PROVIDERS.includes(provider))
              .map((provider) => (
                <AutocompleteItem key={provider}>
                  {mapProvider(provider)}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
        </Autocomplete>
      </fieldset>

      <fieldset className="flex flex-col gap-2.5 w-full">
        <label className="text-sm">{t(I18nKey.LLM$MODEL)}</label>
        <Autocomplete
          data-testid="llm-model-input"
          isRequired
          isVirtualized={false}
          name="llm-model-input"
          aria-label={t(I18nKey.LLM$MODEL)}
          placeholder={t(I18nKey.LLM$SELECT_MODEL_PLACEHOLDER)}
          isClearable={false}
          onSelectionChange={(e) => {
            if (e?.toString()) handleChangeModel(e.toString());
          }}
          isDisabled={isDisabled || !selectedProvider}
          selectedKey={selectedModel}
          defaultSelectedKey={selectedModel ?? undefined}
          classNames={{
            popoverContent: "bg-tertiary rounded-xl border border-[#717888]",
          }}
          inputProps={{
            classNames: {
              inputWrapper:
                "bg-tertiary border border-[#717888] h-10 w-full rounded-sm p-2 placeholder:italic",
            },
          }}
        >
          <AutocompleteSection title={t(I18nKey.MODEL_SELECTOR$VERIFIED)}>
            {models[selectedProvider || ""]?.models
              .filter((model) => VERIFIED_MODELS.includes(model))
              .map((model) => (
                <AutocompleteItem key={model}>{model}</AutocompleteItem>
              ))}
          </AutocompleteSection>
          <AutocompleteSection title={t(I18nKey.MODEL_SELECTOR$OTHERS)}>
            {models[selectedProvider || ""]?.models
              .filter((model) => !VERIFIED_MODELS.includes(model))
              .map((model) => (
                <AutocompleteItem
                  data-testid={`model-item-${model}`}
                  key={model}
                >
                  {model}
                </AutocompleteItem>
              ))}
          </AutocompleteSection>
        </Autocomplete>
      </fieldset>
    </div>
  );
}
