import { Tooltip } from "@nextui-org/react";
import { ReactNode } from "react";

interface TooltipButtonProps {
  children: ReactNode;
  tooltip: string;
  onClick?: () => void;
  href?: string;
  ariaLabel: string;
  testId?: string;
}

export function TooltipButton({
  children,
  tooltip,
  onClick,
  href,
  ariaLabel,
  testId,
}: TooltipButtonProps) {
  const buttonContent = (
    <button
      type="button"
      aria-label={ariaLabel}
      data-testid={testId}
      onClick={onClick}
      className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
    >
      {children}
    </button>
  );

  const content = href ? (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
      aria-label={ariaLabel}
    >
      {children}
    </a>
  ) : (
    buttonContent
  );

  return (
    <Tooltip content={tooltip} closeDelay={100}>
      {content}
    </Tooltip>
  );
}
