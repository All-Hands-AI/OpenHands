import React from "react";
import { Toggle } from "@openhands/ui";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

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
  const { t } = useTranslation();
  const [isToggled, setIsToggled] = React.useState(defaultIsToggled ?? false);

  const handleToggle = (value: boolean) => {
    setIsToggled(value);
    onToggle?.(value);
  };

  return (
    <Toggle
      name={name}
      testId={testId}
      checked={controlledIsToggled ?? isToggled}
      onChange={(e) => handleToggle(e.target.checked)}
      label={
        <div className="flex items-center gap-1">
          <span className="text-sm">{children}</span>
          {isBeta && (
            <span className="text-[11px] leading-4 text-[#0D0F11] font-[500] tracking-tighter bg-primary px-1 rounded-full">
              {t(I18nKey.BADGE$BETA)}
            </span>
          )}
        </div>
      }
    />
  );
}
