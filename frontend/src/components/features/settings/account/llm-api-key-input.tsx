import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { HelpLink } from "../help-link";
import { KeyStatusIcon } from "../key-status-icon";
import { SettingsInput } from "../settings-input";

interface LlmApiKeyInputProps {
  isLLMKeySet: boolean;
}

export function LlmApiKeyInput({ isLLMKeySet }: LlmApiKeyInputProps) {
  const { t } = useTranslation();

  return (
    <>
      <SettingsInput
        testId="llm-api-key-input"
        name="llm-api-key-input"
        label={t(I18nKey.SETTINGS_FORM$API_KEY)}
        type="password"
        className="w-[680px]"
        placeholder={isLLMKeySet ? "<hidden>" : ""}
        startContent={isLLMKeySet && <KeyStatusIcon isSet={isLLMKeySet} />}
      />

      <HelpLink
        testId="llm-api-key-help-anchor"
        text={t(I18nKey.SETTINGS$DONT_KNOW_API_KEY)}
        linkText={t(I18nKey.SETTINGS$CLICK_FOR_INSTRUCTIONS)}
        href="https://docs.all-hands.dev/modules/usage/installation#getting-an-api-key"
      />
    </>
  );
}
