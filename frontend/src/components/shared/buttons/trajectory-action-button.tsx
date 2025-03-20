import { Tooltip } from "@heroui/react";

interface TrajectoryActionButtonProps {
  testId?: string;
  onClick: () => void;
  icon: React.ReactNode;
  tooltip?: string;
}

export function TrajectoryActionButton({
  testId,
  onClick,
  icon,
  tooltip,
}: TrajectoryActionButtonProps) {
  const button = (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      className="button-base p-1 hover:bg-neutral-500"
    >
      {icon}
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
