import { Tooltip } from "@heroui/react";
import { useState } from "react";

interface ToggleSwitchButtonProps {
  testId?: string;
  onClick: (isOn: boolean) => void;
  tooltip?: string;
  defaultOn?: boolean;
}

export function ToggleSwitchButton({
  testId,
  onClick,
  tooltip,
  defaultOn = false,
}: ToggleSwitchButtonProps) {
  const [isOn, setIsOn] = useState(defaultOn);

  const handleClick = () => {
    const newState = !isOn;
    setIsOn(newState);
    onClick(newState);
  };

  const button = (
    <button
      type="button"
      data-testid={testId}
      onClick={handleClick}
      className="button-base p-1 hover:bg-neutral-500 relative w-8 h-6 rounded-full transition-colors duration-200"
      style={{ backgroundColor: isOn ? "#4CAF50" : "#666" }}
    >
      <div
        className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform duration-200"
        style={{ transform: isOn ? "translateX(100%)" : "translateX(0)" }}
      />
    </button>
  );

  if (tooltip) {
    return (
      <Tooltip content={tooltip} closeDelay={100}>
        {button}
      </Tooltip>
    );
  }

  return button;
}
