import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

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
    <TooltipButton
      tooltip={tooltipMessage}
      ariaLabel={tooltipMessage}
      testId={testId}
      placement="top"
      className="hover:opacity-100"
      tooltipClassName="bg-white text-black"
      showArrow
    >
      {children}
    </TooltipButton>
  );
}
