import { UnifiedButton } from "#/ui/unified-button/unified-button";

interface GitControlBarTooltipWrapperProps {
  tooltipMessage: string;
  testId: string;
  children: React.ReactNode;
  shouldShowTooltip: boolean;
}

export function GitControlBarTooltipWrapper({
  children,
  tooltipMessage,
  testId,
  shouldShowTooltip,
}: GitControlBarTooltipWrapperProps) {
  if (!shouldShowTooltip) {
    return children;
  }

  return (
    <UnifiedButton
      withTooltip
      tooltipContent={tooltipMessage}
      ariaLabel={tooltipMessage}
      testId={testId}
      tooltipProps={{
        placement: "top",
        className: "bg-white text-black",
        showArrow: true,
      }}
      className="bg-transparent hover:bg-transparent hover:opacity-100"
    >
      {children}
    </UnifiedButton>
  );
}
