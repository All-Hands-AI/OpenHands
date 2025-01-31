import React from "react";
import { OptionalTag } from "./optional-tag";
import { StyledSwitchComponent } from "./styled-switch-component";

interface SettingsSwitchProps {
  testId?: string;
  showOptionalTag?: boolean;
  onToggle?: (value: boolean) => void;
  defaultIsToggled?: boolean;
}

export function SettingsSwitch({
  children,
  testId,
  showOptionalTag,
  onToggle,
  defaultIsToggled,
}: React.PropsWithChildren<SettingsSwitchProps>) {
  const [isToggled, setIsToggled] = React.useState(defaultIsToggled ?? false);

  const handleToggle = (value: boolean) => {
    setIsToggled(value);
    onToggle?.(value);
  };

  return (
    <label className="flex items-center gap-2 w-fit">
      <input
        hidden
        data-testid={testId}
        type="checkbox"
        onChange={(e) => handleToggle(e.target.checked)}
        defaultChecked={defaultIsToggled}
      />

      <StyledSwitchComponent isToggled={isToggled} />

      <div className="flex items-center gap-1">
        <span className="text-sm">{children}</span>
        {showOptionalTag && <OptionalTag />}
      </div>
    </label>
  );
}
