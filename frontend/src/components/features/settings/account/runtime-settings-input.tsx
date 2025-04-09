import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";

// Define REMOTE_RUNTIME_OPTIONS for testing
const REMOTE_RUNTIME_OPTIONS = [
  { key: "1", label: "Standard" },
  { key: "2", label: "Enhanced" },
  { key: "4", label: "Premium" },
];

interface RuntimeSettingsInputProps {
  defaultRuntime?: string;
}

export function RuntimeSettingsInput({
  defaultRuntime,
}: RuntimeSettingsInputProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="runtime-settings-input"
      name="runtime-settings-input"
      label={
        <>
          {t(I18nKey.SETTINGS$RUNTIME_SETTINGS)}
          <a href="mailto:contact@all-hands.dev">
            {t(I18nKey.SETTINGS$GET_IN_TOUCH)}
          </a>
        </>
      }
      items={REMOTE_RUNTIME_OPTIONS}
      defaultSelectedKey={defaultRuntime}
      isDisabled
      isClearable={false}
    />
  );
}
