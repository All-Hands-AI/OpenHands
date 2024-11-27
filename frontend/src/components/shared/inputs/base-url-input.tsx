import { Input } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface BaseUrlInputProps {
  isDisabled: boolean;
  defaultValue: string;
}

export function BaseUrlInput({ isDisabled, defaultValue }: BaseUrlInputProps) {
  const { t } = useTranslation();

  return (
    <fieldset className="flex flex-col gap-2">
      <label htmlFor="base-url" className="font-[500] text-[#A3A3A3] text-xs">
        {t(I18nKey.SETTINGS_FORM$BASE_URL_LABEL)}
      </label>
      <Input
        isDisabled={isDisabled}
        id="base-url"
        name="base-url"
        defaultValue={defaultValue}
        aria-label="Base URL"
        classNames={{
          inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
        }}
      />
    </fieldset>
  );
}
