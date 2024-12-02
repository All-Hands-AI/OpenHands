import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface AgentInputProps {
  isDisabled: boolean;
  defaultValue: string;
  agents: string[];
}

export function AgentInput({
  isDisabled,
  defaultValue,
  agents,
}: AgentInputProps) {
  const { t } = useTranslation();

  return (
    <fieldset data-testid="agent-selector" className="flex flex-col gap-2">
      <label htmlFor="agent" className="font-[500] text-[#A3A3A3] text-xs">
        {t(I18nKey.SETTINGS_FORM$AGENT_LABEL)}
      </label>
      <Autocomplete
        isDisabled={isDisabled}
        isRequired
        id="agent"
        aria-label="Agent"
        data-testid="agent-input"
        name="agent"
        defaultSelectedKey={defaultValue}
        isClearable={false}
        inputProps={{
          classNames: {
            inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
          },
        }}
      >
        {agents.map((agent) => (
          <AutocompleteItem key={agent} value={agent}>
            {agent}
          </AutocompleteItem>
        ))}
      </Autocomplete>
    </fieldset>
  );
}
