import { Tooltip } from "@heroui/react";
import { useSelector } from "react-redux";
import MoneyIcon from "#/icons/money.svg?react";
import { RootState } from "#/store";

interface CostToggleButtonProps {
  testId: string;
  onClick: (isVisible: boolean) => void;
  tooltip?: string;
}

export function CostToggleButton({
  testId,
  onClick,
  tooltip,
}: CostToggleButtonProps) {
  const isVisible = useSelector((state: RootState) => state.costVisibility.isVisible);

  const handleClick = () => {
    onClick(!isVisible);
  };

  const button = (
    <button
      type="button"
      data-testid={testId}
      onClick={handleClick}
      className={`button-base p-1 ${isVisible ? "" : "opacity-50"} hover:bg-neutral-500`}
    >
      <MoneyIcon width={15} height={15} className="text-gray-400" />
    </button>
  );

  if (tooltip) {
    return <Tooltip content={tooltip} closeDelay={100}>{button}</Tooltip>;
  }

  return button;
}
