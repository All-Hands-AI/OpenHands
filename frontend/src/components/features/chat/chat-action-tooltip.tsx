import { UnifiedButton } from "#/ui/unified-button/unified-button";

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
    <UnifiedButton
      withTooltip
      tooltipContent={tooltip}
      ariaLabel={ariaLabel}
      disabled={false}
      tooltipProps={{
        placement: "bottom",
        className: "bg-white text-black text-xs font-medium leading-5",
      }}
      className="bg-transparent hover:bg-transparent"
    >
      {children}
    </UnifiedButton>
  );
}
