import { Switch } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

interface EnableDefaultCondenserSwitchProps {
  isDisabled: boolean;
  defaultSelected: boolean;
}

export function EnableDefaultCondenserSwitch({
  isDisabled,
  defaultSelected,
}: EnableDefaultCondenserSwitchProps) {
  const { t } = useTranslation();

  return (
    <Switch
      isDisabled={isDisabled}
      name="enable-default-condenser"
      defaultSelected={defaultSelected}
      classNames={{
        thumb: cn(
          "bg-[#5D5D5D] w-3 h-3",
          "group-data-[selected=true]:bg-white",
        ),
        wrapper: cn(
          "border border-[#D4D4D4] bg-white px-[6px] w-12 h-6",
          "group-data-[selected=true]:border-transparent group-data-[selected=true]:bg-[#4465DB]",
        ),
        label: "text-[#A3A3A3] text-xs",
      }}
    >
      {t(I18nKey.SETTINGS_FORM$ENABLE_DEFAULT_CONDENSER_SWITCH_LABEL)}
    </Switch>
  );
}
