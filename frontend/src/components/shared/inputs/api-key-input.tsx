import { Input } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SetBadge } from "#/components/features/set-status/set-badge";
import { UnsetButton } from "#/components/features/set-status/unset-button";

interface APIKeyInputProps {
  isDisabled: boolean;
  isSet: boolean;
  onUnset: () => void;
}

export function APIKeyInput({ isDisabled, isSet, onUnset }: APIKeyInputProps) {
  const { t } = useTranslation();

  return (
    <fieldset className="flex flex-col gap-2">
      <label
        htmlFor="api-key"
        className="font-[500] text-[#A3A3A3] text-xs flex items-center gap-1 self-start"
      >
        <SetBadge isSet={isSet} />
        {t(I18nKey.API$KEY)}
        {isSet && (
          <UnsetButton testId="unset-api-key-button" onUnset={onUnset} />
        )}
      </label>
      {!isSet && (
        <Input
          data-testid="api-key-input"
          isDisabled={isDisabled}
          id="api-key"
          name="api-key"
          aria-label={t(I18nKey.API$KEY)}
          type="password"
          defaultValue=""
          classNames={{
            inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
          }}
        />
      )}
      {isSet && (
        <p className="text-sm text-[#A3A3A3]">
          {t(I18nKey.API$DONT_KNOW_KEY)}{" "}
          <a
            href="https://docs.all-hands.dev/modules/usage/llms"
            rel="noreferrer noopener"
            target="_blank"
            className="underline underline-offset-2"
          >
            {t(I18nKey.COMMON$CLICK_FOR_INSTRUCTIONS)}
          </a>
        </p>
      )}
    </fieldset>
  );
}
