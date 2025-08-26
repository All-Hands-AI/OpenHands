import React from "react";
import { cn } from "#/utils/utils";

interface ToggleButtonProps {
  isOpen: boolean;
  disabled: boolean;
  getToggleButtonProps: any;
}

export function ToggleButton({ isOpen, disabled, getToggleButtonProps }: ToggleButtonProps) {
  return (
    <button
      {...getToggleButtonProps({
        disabled,
        className: cn(
          "p-1 text-gray-400 hover:text-gray-600",
          "disabled:cursor-not-allowed"
        ),
      })}
      type="button"
      aria-label="Toggle menu"
    >
      <svg
        className={cn(
          "w-4 h-4 transition-transform",
          isOpen && "rotate-180"
        )}
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