import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

interface ChatActionTooltipProps {
  children: React.ReactNode;
  tooltip: string | React.ReactNode;
  ariaLabel: string;
}

export function ChatActionTooltip({
  children,
  tooltip,
  ariaLabel,
}: ChatActionTooltipProps) {
  return (
    <TooltipButton
      tooltip={tooltip}
      ariaLabel={ariaLabel}
      disabled={false}
      placement="bottom"
      tooltipClassName="bg-white text-black text-xs font-medium leading-5"
    >
      {children}
    </TooltipButton>
  );
}
