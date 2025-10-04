import { ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { TooltipProps } from "@heroui/react";

// Define variants based ONLY on existing patterns found in the codebase
export const buttonVariants = cva(
  "flex items-center justify-center cursor-pointer transition-all duration-200",
  {
    variants: {
      size: {
        // Based on existing components
        compact: "px-0.5 py-1 gap-1", // from git-control-button
        small: "w-5 h-5", // from remove-button
        medium: "size-[35px]", // from chat-send-button
        large: "w-[26px] h-[26px]", // from trajectory-action-button
      },
      variant: {
        // Based on existing background colors found
        primary: "bg-[#25272D] hover:bg-[#525662]", // from git-control-button
        secondary: "bg-tertiary border border-neutral-600", // from button-base CSS class
        ghost: "bg-transparent", // from icon-button
        neutral: "bg-neutral-400", // from remove-button
      },
      intent: {
        button: "type-button",
        submit: "type-submit",
        reset: "type-reset",
      },
      disabled: {
        true: "opacity-50 cursor-not-allowed",
        false: "",
      },
    },
    defaultVariants: {
      size: "compact",
      variant: "primary",
      intent: "button",
      disabled: false,
    },
  },
);

// Base props that all button types share
export type BaseButtonProps = {
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  testId?: string;
  ariaLabel?: string;
  withTooltip?: boolean;
  tooltipContent?: string | ReactNode;
  tooltipProps?: Omit<TooltipProps, "content" | "children">;
} & VariantProps<typeof buttonVariants>;

// Button element props - only include specific props we want to support
export type ButtonProps = BaseButtonProps & {
  as?: "button";
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
};

// Anchor element props - only include specific props we want to support
export type AnchorProps = BaseButtonProps & {
  as: "a";
  href: string;
  target?: string;
  rel?: string;
  onClick?: () => void;
};

// NavLink props - only include specific props we want to support
export type NavLinkProps = BaseButtonProps & {
  as: "NavLink";
  to: string;
  onClick?: () => void;
  // Allow parent components to control active/inactive styles
  activeClassName?: string;
  inactiveClassName?: string;
};

export type UnifiedButtonProps = ButtonProps | AnchorProps | NavLinkProps;
