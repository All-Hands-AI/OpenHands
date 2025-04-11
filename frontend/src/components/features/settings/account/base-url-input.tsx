import { useTranslation } from "react-i18next";
import { SettingsInput } from "../settings-input";
import { I18nKey } from "#/i18n/declaration";

interface BaseUrlInputProps {
  defaultBaseUrl: string;
}

export function BaseUrlInput({ defaultBaseUrl }: BaseUrlInputProps) {
  const { t } = useTranslation();

  return (
    <SettingsInput
      testId="base-url-input"
      name="base-url-input"
      label={t(I18nKey.SETTINGS$BASE_URL)}
      defaultValue={defaultBaseUrl}
      placeholder="https://api.openai.com"
      type="text"
      className="w-[680px]"
    />
  );
}
