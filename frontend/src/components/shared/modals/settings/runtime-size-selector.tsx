import React from "react";
import { useTranslation } from "react-i18next";
import { Select, SelectItem } from "@nextui-org/react";
import { useConfig } from "#/hooks/query/use-config";

interface RuntimeSizeSelectorProps {
  isDisabled: boolean;
  defaultValue?: number;
}

export function RuntimeSizeSelector({
  isDisabled,
  defaultValue,
}: RuntimeSizeSelectorProps) {
  const { t } = useTranslation();
  const { data: config } = useConfig();
  const isSaasMode = config?.saas_mode ?? false;

  if (!isSaasMode) {
    return null;
  }

  return (
    <fieldset className="flex flex-col gap-2">
      <label
        htmlFor="runtime-size"
        className="font-[500] text-[#A3A3A3] text-xs"
      >
        {t("Runtime Size")}
      </label>
      <Select
        id="runtime-size"
        name="runtime-size"
        defaultSelectedKey={String(defaultValue || 1)}
        isDisabled={isDisabled}
        isClearable={false}
        classNames={{
          trigger: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
        }}
      >
        <SelectItem key="1" value={1}>
          {t("1x (2 core, 8G)")}
        </SelectItem>
        <SelectItem key="2" value={2}>
          {t("2x (4 core, 16G)")}
        </SelectItem>
      </Select>
    </fieldset>
  );
}
