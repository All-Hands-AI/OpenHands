import { Tooltip } from "@heroui/react";
import React, { ReactNode } from "react";
import { NavLink } from "react-router";
import { cn } from "#/utils/utils";

export interface TooltipButtonProps {
  children: ReactNode;
  tooltip: string;
  onClick?: () => void;
  href?: string;
  navLinkTo?: string;
  ariaLabel: string;
  testId?: string;
  className?: React.HTMLAttributes<HTMLButtonElement>["className"];
}

export function TooltipButton({
  children,
  tooltip,
  onClick,
  href,
  navLinkTo,
  ariaLabel,
  testId,
  className,
}: TooltipButtonProps) {
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
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

  let content;

  if (navLinkTo) {
    content = (
      <NavLink
        to={navLinkTo}
        onClick={handleClick}
        className={({ isActive }) =>
          cn(
            "hover:opacity-80",
            isActive ? "text-white" : "text-[#9099AC]",
            className,
          )
        }
        aria-label={ariaLabel}
        data-testid={testId}
      >
        {children}
      </NavLink>
    );
  } else if (href) {
    content = (
      <a
        href={href}
        target="_blank"
        rel="noreferrer noopener"
        className={cn("hover:opacity-80", className)}
        aria-label={ariaLabel}
        data-testid={testId}
      >
        {children}
      </a>
    );
  } else {
    content = buttonContent;
  }

  return (
    <Tooltip content={tooltip} closeDelay={100} placement="right">
      {content}
    </Tooltip>
  );
}
