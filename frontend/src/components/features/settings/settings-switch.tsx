import React from "react"
import { StyledSwitchComponent } from "./styled-switch-component"

interface SettingsSwitchProps {
  testId?: string
  name?: string
  onToggle?: (value: boolean) => void
  defaultIsToggled?: boolean
  isBeta?: boolean
}

export function SettingsSwitch({
  children,
  testId,
  name,
  onToggle,
  defaultIsToggled,
  isBeta,
}: React.PropsWithChildren<SettingsSwitchProps>) {
  const [isToggled, setIsToggled] = React.useState(defaultIsToggled ?? false)

  const handleToggle = (value: boolean) => {
    setIsToggled(value)
    onToggle?.(value)
  }

  return (
    <label className="flex w-fit items-center gap-2">
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
        <span className="text-[14px] font-medium text-neutral-700 dark:text-[#979995]">
          {children}
        </span>
        {isBeta && (
          <span className="rounded-full bg-primary px-1 text-[11px] font-[500] leading-4 tracking-tighter text-[#0D0F11]">
            Beta
          </span>
        )}
      </div>
    </label>
  )
}
