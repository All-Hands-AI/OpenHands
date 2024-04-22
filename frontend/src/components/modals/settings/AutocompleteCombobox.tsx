import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "../../../i18n/declaration";

type Label = "model" | "agent" | "language";

const LABELS: Record<Label, I18nKey> = {
  model: I18nKey.CONFIGURATION$MODEL_SELECT_LABEL,
  agent: I18nKey.CONFIGURATION$AGENT_SELECT_LABEL,
  language: I18nKey.CONFIGURATION$LANGUAGE_SELECT_LABEL,
};

const PLACEHOLDERS: Record<Label, I18nKey> = {
  model: I18nKey.CONFIGURATION$MODEL_SELECT_PLACEHOLDER,
  agent: I18nKey.CONFIGURATION$AGENT_SELECT_PLACEHOLDER,
  language: I18nKey.CONFIGURATION$LANGUAGE_SELECT_PLACEHOLDER,
};

type AutocompleteItemType = {
  value: string;
  label: string;
};

interface AutocompleteComboboxProps {
  ariaLabel: Label;
  items: AutocompleteItemType[];
  defaultKey: string;
  onChange: (key: string) => void;
  allowCustomValue?: boolean;
}

export function AutocompleteCombobox({
  ariaLabel,
  items,
  defaultKey,
  onChange,
  allowCustomValue = false,
}: AutocompleteComboboxProps) {
  const { t } = useTranslation();

  return (
    <Autocomplete
      aria-label={ariaLabel}
      label={t(LABELS[ariaLabel])}
      placeholder={t(PLACEHOLDERS[ariaLabel])}
      defaultItems={items}
      defaultSelectedKey={defaultKey}
      allowsCustomValue={allowCustomValue}
      onInputChange={(value) => {
        onChange(value);
      }}
    >
      {(item) => (
        <AutocompleteItem key={item.value}>{item.label}</AutocompleteItem>
      )}
    </Autocomplete>
  );
}

AutocompleteCombobox.defaultProps = {
  allowCustomValue: false,
};
