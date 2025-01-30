import { OptionalTag } from "./optional-tag";

interface SettingsSwitchProps {
  testId?: string;
  showOptionalTag?: boolean;
}

export function SettingsSwitch({
  testId,
  showOptionalTag,
}: React.PropsWithChildren<SettingsSwitchProps>) {
  return (
    <label className="flex items-center gap-2">
      <input data-testid={testId} type="checkbox" />
      <div className="flex items-center gap-1">
        <span className="text-sm">Enable analytics</span>
        {showOptionalTag && <OptionalTag />}
      </div>
    </label>
  );
}
