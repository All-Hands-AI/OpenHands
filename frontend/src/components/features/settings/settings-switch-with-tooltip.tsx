import React from "react";
import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { StyledSwitchComponent } from "./styled-switch-component";
import QuestionCircleIcon from "#/icons/question-circle.svg?react";

interface SettingsSwitchWithTooltipProps {
  testId?: string;
  name?: string;
  onToggle?: (value: boolean) => void;
  defaultIsToggled?: boolean;
  isToggled?: boolean;
  isBeta?: boolean;
  tooltip: string;
}

export function SettingsSwitchWithTooltip({
  children,
  testId,
  name,
  onToggle,
  defaultIsToggled,
  isToggled: controlledIsToggled,
  isBeta,
  tooltip,
}: React.PropsWithChildren<SettingsSwitchWithTooltipProps>) {
  const { t } = useTranslation();
  const [isToggled, setIsToggled] = React.useState(defaultIsToggled ?? false);

  const handleToggle = (value: boolean) => {
    setIsToggled(value);
    onToggle?.(value);
  };

  return (
    <label className="flex items-center gap-2 w-fit cursor-pointer">
      <input
        hidden
        data-testid={testId}
        name={name}
        type="checkbox"
        onChange={(e) => handleToggle(e.target.checked)}
        checked={controlledIsToggled ?? isToggled}
      />

      <StyledSwitchComponent isToggled={controlledIsToggled ?? isToggled} />

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          <span className="text-sm">{children}</span>
          {isBeta && (
            <span className="text-[11px] leading-4 text-[#0D0F11] font-[500] tracking-tighter bg-primary px-1 rounded-full">
              {t(I18nKey.BADGE$BETA)}
            </span>
          )}
        </div>
        <Tooltip
          content={tooltip}
          closeDelay={100}
          placement="right"
          className="max-w-xs"
        >
          <QuestionCircleIcon
            width={16}
            height={16}
            className="text-[#9099AC] hover:text-white cursor-help"
            aria-label="Information"
          />
        </Tooltip>
      </div>
    </label>
  );
}
