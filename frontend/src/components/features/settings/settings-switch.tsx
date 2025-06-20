import React from "react";
import { Switch } from "@heroui/react";
import { cn } from "#/utils/utils";

interface SettingsSwitchProps {
  testId?: string;
  name?: string;
  onToggle?: (value: boolean) => void;
  defaultIsToggled?: boolean;
  isToggled?: boolean;
  isBeta?: boolean;
}

export function SettingsSwitch({
  children,
  testId,
  name,
  onToggle,
  defaultIsToggled,
  isToggled: controlledIsToggled,
  isBeta,
}: React.PropsWithChildren<SettingsSwitchProps>) {
  const [isToggled, setIsToggled] = React.useState(defaultIsToggled ?? false);

  const isControlled = controlledIsToggled !== undefined;
  const checked = isControlled ? controlledIsToggled : isToggled;

  const handleToggle = (value: boolean) => {
    if (!isControlled) setIsToggled(value);
    onToggle?.(value);
  };

  return (
    <label className="flex items-center gap-2 w-fit cursor-pointer">
      <Switch
        data-testid={testId}
        name={name}
        isSelected={checked}
        onValueChange={handleToggle}
        classNames={{
          thumb: cn(
            "bg-[#5D5D5D] w-3 h-3",
            "group-data-[selected=true]:bg-white",
          ),
          wrapper: cn(
            "border border-[#D4D4D4] bg-white px-[6px] w-12 h-6",
            "group-data-[selected=true]:border-transparent group-data-[selected=true]:bg-[#4465DB]",
          ),
        }}
      />
      <div className="flex items-center gap-1">
        <span className="text-sm text-content">{children}</span>
        {isBeta && (
          <span className="text-[11px] leading-4 text-[#0D0F11] font-[500] tracking-tighter bg-primary px-1 rounded-full">
            Beta
          </span>
        )}
      </div>
    </label>
  );
}
