import { OptionalTag } from "./optional-tag";

interface SettingsSwitchProps {
  testId?: string;
  showOptionalTag?: boolean;
  onToggle?: (value: boolean) => void;
}

export function SettingsSwitch({
  children,
  testId,
  showOptionalTag,
  onToggle,
}: React.PropsWithChildren<SettingsSwitchProps>) {
  return (
    <label className="flex items-center gap-2 w-fit">
      <input
        data-testid={testId}
        type="checkbox"
        onChange={(e) => onToggle?.(e.target.checked)}
      />
      <div className="flex items-center gap-1">
        <span className="text-sm">{children}</span>
        {showOptionalTag && <OptionalTag />}
      </div>
    </label>
  );
}
