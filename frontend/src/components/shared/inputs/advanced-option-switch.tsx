import { Switch } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

interface AdvancedOptionSwitchProps {
  isDisabled: boolean;
  showAdvancedOptions: boolean;
  setShowAdvancedOptions: (value: boolean) => void;
}

export function AdvancedOptionSwitch({
  isDisabled,
  showAdvancedOptions,
  setShowAdvancedOptions,
}: AdvancedOptionSwitchProps) {
  const { t } = useTranslation();

  return (
    <Switch
      data-testid="advanced-option-switch"
      isDisabled={isDisabled}
      name="use-advanced-options"
      defaultSelected={showAdvancedOptions}
      onValueChange={setShowAdvancedOptions}
      classNames={{
        thumb: cn(
          "bg-[#5D5D5D] w-3 h-3 z-0",
          "group-data-[selected=true]:bg-white",
        ),
        wrapper: cn(
          "border border-[#D4D4D4] bg-white px-[6px] w-12 h-6",
          "group-data-[selected=true]:border-transparent group-data-[selected=true]:bg-[#4465DB]",
        ),
        label: "text-[#A3A3A3] text-xs",
      }}
    >
      {t(I18nKey.SETTINGS_FORM$ADVANCED_OPTIONS_LABEL)}
    </Switch>
  );
}
