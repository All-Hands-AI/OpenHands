import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";

interface LlmCustomModelInputProps {
  defaultModel: string;
}

export function LlmCustomModelInput({
  defaultModel,
}: LlmCustomModelInputProps) {
  const { t } = useTranslation();

  return (
    <SettingsInput
      testId="llm-custom-model-input"
      name="llm-custom-model-input"
      label={t(I18nKey.SETTINGS$CUSTOM_MODEL)}
      defaultValue={defaultModel}
      placeholder="anthropic/claude-3-5-sonnet-20241022"
      type="text"
      className="w-[680px]"
    />
  );
}
