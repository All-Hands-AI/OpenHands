import { useSettings } from "#/hooks/query/use-settings";
import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
} from "@heroui/react";

interface ProviderSelectorProps {
  selectedProvider: string | null;
  setSelectedProvider: (value: string | null) => void;
}

export function ProviderSelector({
  selectedProvider,
  setSelectedProvider,
}: ProviderSelectorProps) {
  const { data: settings } = useSettings();

  const providerSet = settings?.PROVIDER_TOKENS_SET || {};

  const handleProviderSelection = (provider: string | null) => {
    setSelectedProvider(provider);
  };

  return (
    <>
      <Autocomplete
        data-testid="provider-selector"
        name="provider"
        aria-label="Git Provider"
        placeholder="Select Git Provider"
        isVirtualized={false}
        selectedKey={selectedProvider}
        inputProps={{
          classNames: {
            inputWrapper:
              "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
          },
        }}
        onSelectionChange={(id) =>
          handleProviderSelection(id?.toString() ?? null)
        }
      >
        {Object.keys(providerSet).length > 0 ? (
          <AutocompleteSection>
            {Object.keys(providerSet).map((provider) => (
              <AutocompleteItem key={provider} textValue={provider}>
                {provider}
              </AutocompleteItem>
            ))}
          </AutocompleteSection>
        ) : null}
      </Autocomplete>
    </>
  );
}
