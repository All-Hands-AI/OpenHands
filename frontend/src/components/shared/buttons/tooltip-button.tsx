import { Tooltip } from "@heroui/react";
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
  // Handle click with support for cmd/ctrl+click to open in new tab
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      // If cmd/ctrl key is pressed, let the default behavior happen (open in new tab)
      if (e.metaKey || e.ctrlKey) {
        // Don't prevent default to allow browser to handle opening in new tab
        return;
      }

      // Otherwise, call the onClick handler
      onClick();
      e.preventDefault();
    }
  };

  const buttonContent = (
    <button
      type="button"
      aria-label={ariaLabel}
      data-testid={testId}
      onClick={handleClick}
      className={cn("hover:opacity-80", className)}
    >
      {children}
    </button>
  );

  const content = href ? (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className={cn("hover:opacity-80", className)}
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
