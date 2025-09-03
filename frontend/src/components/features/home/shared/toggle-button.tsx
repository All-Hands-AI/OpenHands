import React from "react";
import { cn } from "#/utils/utils";

interface ToggleButtonProps {
  isOpen: boolean;
  disabled: boolean;
  getToggleButtonProps: (
    props?: Record<string, unknown>,
  ) => Record<string, unknown>;
}

export function ToggleButton({
  isOpen,
  disabled,
  getToggleButtonProps,
}: ToggleButtonProps) {
  return (
    <button
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...getToggleButtonProps({
        disabled,
        className: cn(
          "p-1 text-[#B7BDC2] hover:text-[#ECEDEE]",
          "disabled:cursor-not-allowed disabled:opacity-60",
        ),
      })}
      type="button"
      aria-label="Toggle menu"
    >
      <svg
        className={cn("w-4 h-4 transition-transform", isOpen && "rotate-180")}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>
  );
}
