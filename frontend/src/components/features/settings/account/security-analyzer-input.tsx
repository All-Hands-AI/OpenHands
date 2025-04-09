import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";

interface SecurityAnalzerInputProps {
  securityAnalyzers: string[];
  defaultSecurityAnalyzer: string;
}

export function SecurityAnalzerInput({
  defaultSecurityAnalyzer,
  securityAnalyzers,
}: SecurityAnalzerInputProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="security-analyzer-input"
      name="security-analyzer-input"
      label={t(I18nKey.SETTINGS$SECURITY_ANALYZER)}
      items={securityAnalyzers.map((analyzer) => ({
        key: analyzer,
        label: analyzer,
      }))}
      defaultSelectedKey={defaultSecurityAnalyzer}
      isClearable
      showOptionalTag
    />
  );
}
