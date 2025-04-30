import React from "react";
import { StyledSwitchComponent } from "./styled-switch-component";

interface SettingsSwitchProps {
  testId?: string;
  name?: string;
  onToggle?: (value: boolean) => void;
  defaultIsToggled?: boolean;
  isBeta?: boolean;
}

export function SettingsSwitch({
  children,
  testId,
  name,
  onToggle,
  defaultIsToggled,
  isBeta,
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
        name={name}
        type="checkbox"
        onChange={(e) => handleToggle(e.target.checked)}
        defaultChecked={defaultIsToggled}
      />

      <StyledSwitchComponent isToggled={isToggled} />

      <div className="flex items-center gap-1">
        <span className="text-sm">{children}</span>
        {isBeta && (
          <span className="text-[11px] leading-4 text-[#0D0F11] font-[500] tracking-tighter bg-primary px-1 rounded-full">
            Beta
          </span>
        )}
      </div>
    </label>
  );
}
