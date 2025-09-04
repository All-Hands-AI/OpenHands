import { ReactNode } from "react";
import { NavLink } from "react-router";
import { Tooltip } from "@heroui/react";
import { cn } from "#/utils/utils";
import {
  buttonVariants,
  type UnifiedButtonProps,
  type AnchorProps,
  type NavLinkProps,
  type ButtonProps,
} from "./unified-button.types";

const getButtonType = (
  intent: "button" | "submit" | "reset",
): "button" | "submit" | "reset" => {
  switch (intent) {
    case "submit":
      return "submit";
    case "reset":
      return "reset";
    default:
      return "button";
  }
};

/* eslint-disable react/jsx-props-no-spreading */
/* eslint-disable react/button-has-type */
export function UnifiedButton({
  size,
  variant,
  intent,
  disabled = false,
  children,
  className,
  testId,
  ariaLabel,
  withTooltip = false,
  tooltipContent,
  tooltipProps,
  ...restProps
}: UnifiedButtonProps) {
  // Determine the component type
  const isAnchor = (restProps as AnchorProps).as === "a";
  const isNavLink = (restProps as NavLinkProps).as === "NavLink";

  // Base button classes
  const buttonClasses = cn(
    buttonVariants({ size, variant, intent, disabled }),
    className,
  );

  // Common props for all button types
  const commonProps = {
    "data-testid": testId,
    "aria-label": ariaLabel,
    className: buttonClasses,
  };

  // Render content with or without tooltip
  const renderContent = (content: ReactNode) => {
    if (withTooltip && tooltipContent) {
      return (
        <Tooltip content={tooltipContent} closeDelay={100} {...tooltipProps}>
          {content}
        </Tooltip>
      );
    }
    return content;
  };

  // Render anchor element
  if (isAnchor) {
    const anchorProps = restProps as AnchorProps;
    const content = (
      <a
        {...commonProps}
        href={anchorProps.href}
        target={anchorProps.target}
        rel={anchorProps.rel}
        onClick={anchorProps.onClick}
      >
        {children}
      </a>
    );
    return renderContent(content);
  }

  // Render NavLink element
  if (isNavLink) {
    const navLinkProps = restProps as NavLinkProps;
    const content = (
      <NavLink
        {...commonProps}
        to={navLinkProps.to}
        onClick={navLinkProps.onClick}
        className={({ isActive }) =>
          cn(
            buttonClasses,
            isActive
              ? navLinkProps.activeClassName || "text-white"
              : navLinkProps.inactiveClassName || "text-gray-400",
          )
        }
      >
        {children}
      </NavLink>
    );
    return renderContent(content);
  }

  // Render button element (default)
  const buttonProps = restProps as ButtonProps;
  const content = (
    <button
      {...commonProps}
      type={getButtonType(intent || "button") || "button"}
      disabled={disabled}
      onClick={buttonProps.onClick}
    >
      {children}
    </button>
  );
  return renderContent(content);
}
