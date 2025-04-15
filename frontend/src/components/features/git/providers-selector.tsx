import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
} from "@heroui/react";
import { useAuth } from "#/context/auth-context";
import { Provider } from "#/types/settings";

interface ProviderSelectorProps {
  selectedProvider: Provider | null;
  setSelectedProvider: (value: Provider | null) => void;
}

const PROVIDER_LABELS: Record<string, string> = {
  github: "GitHub",
  gitlab: "GitLab",
};

export function ProviderSelector({
  selectedProvider,
  setSelectedProvider,
}: ProviderSelectorProps) {
  const { providerTokensSet } = useAuth();

  const handleProviderSelection = (provider: string | null) => {
    setSelectedProvider(provider as Provider);
  };

  return (
    <Autocomplete
      data-testid="provider-selector"
      name="provider"
      aria-label="Git Provider"
      placeholder="Select Git Provider"
      isVirtualized={false}
      selectedKey={selectedProvider}
      inputValue={
        selectedProvider
          ? (PROVIDER_LABELS[selectedProvider] ?? selectedProvider)
          : ""
      }
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
      {providerTokensSet.length > 0 ? (
        <AutocompleteSection>
          {providerTokensSet.map((provider) => (
            <AutocompleteItem key={provider} textValue={provider}>
              {PROVIDER_LABELS[provider] ?? provider}
            </AutocompleteItem>
          ))}
        </AutocompleteSection>
      ) : null}
    </Autocomplete>
  );
}
