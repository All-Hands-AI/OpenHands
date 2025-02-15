import { Input } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface CustomModelInputProps {
  isDisabled: boolean;
  defaultValue: string;
}

export function CustomModelInput({
  isDisabled,
  defaultValue,
}: CustomModelInputProps) {
  const { t } = useTranslation();

  return (
    <fieldset className="flex flex-col gap-2">
      <label
        htmlFor="custom-model"
        className="font-[500] text-[#A3A3A3] text-xs"
      >
        {t(I18nKey.SETTINGS_FORM$CUSTOM_MODEL_LABEL)}
      </label>
      <Input
        data-testid="custom-model-input"
        isDisabled={isDisabled}
        isRequired
        id="custom-model"
        name="custom-model"
        defaultValue={defaultValue}
        aria-label="Custom Model"
        classNames={{
          inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
        }}
      />
    </fieldset>
  );
}
