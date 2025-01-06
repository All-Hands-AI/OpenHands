import { Tooltip } from "@nextui-org/react";
import React, { ReactNode } from "react";
import { cn } from "#/utils/utils";

interface TooltipButtonProps {
  children: ReactNode;
  tooltip: string;
  onClick?: () => void;
  href?: string;
  ariaLabel: string;
  testId?: string;
  className?: React.HTMLAttributes<HTMLButtonElement>["className"];
}

export function TooltipButton({
  children,
  tooltip,
  onClick,
  href,
  ariaLabel,
  testId,
  className,
}: TooltipButtonProps) {
  const buttonContent = (
    <button
      type="button"
      aria-label={ariaLabel}
      data-testid={testId}
      onClick={onClick}
      className={cn(
        "w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center",
        className,
      )}
    >
      {children}
    </button>
  );

  const content = href ? (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className={cn(
        "w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center",
        className,
      )}
      aria-label={ariaLabel}
    >
      {children}
    </a>
  ) : (
    buttonContent
  );

  return (
    <Tooltip content={tooltip} closeDelay={100} placement="right">
      {content}
    </Tooltip>
  );
}
