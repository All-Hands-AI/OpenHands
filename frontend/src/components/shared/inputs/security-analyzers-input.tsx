import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface SecurityAnalyzerInputProps {
  isDisabled: boolean;
  defaultValue: string;
  securityAnalyzers: string[];
}

export function SecurityAnalyzerInput({
  isDisabled,
  defaultValue,
  securityAnalyzers,
}: SecurityAnalyzerInputProps) {
  const { t } = useTranslation();

  return (
    <fieldset className="flex flex-col gap-2">
      <label
        htmlFor="security-analyzer"
        className="font-[500] text-[#A3A3A3] text-xs"
      >
        {t(I18nKey.SETTINGS_FORM$SECURITY_ANALYZER_LABEL)}
      </label>
      <Autocomplete
        isDisabled={isDisabled}
        id="security-analyzer"
        name="security-analyzer"
        aria-label="Security Analyzer"
        defaultSelectedKey={defaultValue}
        inputProps={{
          classNames: {
            inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
          },
        }}
      >
        {securityAnalyzers.map((analyzer) => (
          <AutocompleteItem key={analyzer} value={analyzer}>
            {analyzer}
          </AutocompleteItem>
        ))}
      </Autocomplete>
    </fieldset>
  );
}
