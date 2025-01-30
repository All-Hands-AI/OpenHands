import { OptionalTag } from "./optional-tag";

interface SettingsSwitchProps {
  testId?: string;
  showOptionalTag?: boolean;
}

export function SettingsSwitch({
  children,
  testId,
  showOptionalTag,
}: React.PropsWithChildren<SettingsSwitchProps>) {
  return (
    <label className="flex items-center gap-2">
      <input data-testid={testId} type="checkbox" />
      <div className="flex items-center gap-1">
        <span className="text-sm">{children}</span>
        {showOptionalTag && <OptionalTag />}
      </div>
    </label>
  );
}
