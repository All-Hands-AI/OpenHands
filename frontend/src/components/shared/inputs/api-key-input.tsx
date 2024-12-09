import { Input } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface APIKeyInputProps {
  isDisabled: boolean;
  defaultValue: string;
}

export function APIKeyInput({ isDisabled, defaultValue }: APIKeyInputProps) {
  const { t } = useTranslation();

  return (
    <fieldset data-testid="api-key-input" className="flex flex-col gap-2">
      <label htmlFor="api-key" className="font-[500] text-[#A3A3A3] text-xs">
        {t(I18nKey.SETTINGS_FORM$API_KEY_LABEL)}
      </label>
      <Input
        isDisabled={isDisabled}
        id="api-key"
        name="api-key"
        aria-label="API Key"
        type="password"
        defaultValue={defaultValue}
        classNames={{
          inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
        }}
      />
      <p className="text-sm text-[#A3A3A3]">
        {t(I18nKey.SETTINGS_FORM$DONT_KNOW_API_KEY_LABEL)}{" "}
        <a
          href="https://docs.all-hands.dev/modules/usage/llms"
          rel="noreferrer noopener"
          target="_blank"
          className="underline underline-offset-2"
        >
          {t(I18nKey.SETTINGS_FORM$CLICK_HERE_FOR_INSTRUCTIONS_LABEL)}
        </a>
      </p>
    </fieldset>
  );
}
