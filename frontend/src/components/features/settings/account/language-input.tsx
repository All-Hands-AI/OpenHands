import { useTranslation } from "react-i18next";
import { AvailableLanguages } from "#/i18n";
import { I18nKey } from "#/i18n/declaration";
import { SettingsDropdownInput } from "../settings-dropdown-input";

interface LanguageInputProps {
  defaultLanguage: string;
}

export function LanguageInput({ defaultLanguage }: LanguageInputProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="language-input"
      name="language-input"
      label={t(I18nKey.SETTINGS$LANGUAGE)}
      items={AvailableLanguages.map((language) => ({
        key: language.value,
        label: language.label,
      }))}
      defaultSelectedKey={defaultLanguage}
      isClearable={false}
    />
  );
}
