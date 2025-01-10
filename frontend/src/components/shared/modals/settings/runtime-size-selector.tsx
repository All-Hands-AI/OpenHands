import { useTranslation } from "react-i18next";
import { Select, SelectItem } from "@nextui-org/react";

interface RuntimeSizeSelectorProps {
  isDisabled: boolean;
  defaultValue?: number;
}

export function RuntimeSizeSelector({
  isDisabled,
  defaultValue,
}: RuntimeSizeSelectorProps) {
  const { t } = useTranslation();

  return (
    <fieldset className="flex flex-col gap-2">
      <label
        htmlFor="runtime-size"
        className="font-[500] text-[#A3A3A3] text-xs"
      >
        {t("SETTINGS_FORM$RUNTIME_SIZE_LABEL")}
      </label>
      <Select
        data-testid="runtime-size"
        id="runtime-size"
        name="runtime-size"
        defaultSelectedKeys={[String(defaultValue || 1)]}
        isDisabled={isDisabled}
        aria-label={t("SETTINGS_FORM$RUNTIME_SIZE_LABEL")}
        classNames={{
          trigger: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
        }}
      >
        <SelectItem key="1" value={1}>
          1x (2 core, 8G)
        </SelectItem>
        <SelectItem
          key="2"
          value={2}
          isDisabled
          classNames={{
            description:
              "whitespace-normal break-words min-w-[300px] max-w-[300px]",
            base: "min-w-[300px] max-w-[300px]",
          }}
          description="Runtime sizes over 1 are disabled by default, please contact contact@all-hands.dev to get access to larger runtimes."
        >
          2x (4 core, 16G)
        </SelectItem>
      </Select>
    </fieldset>
  );
}
