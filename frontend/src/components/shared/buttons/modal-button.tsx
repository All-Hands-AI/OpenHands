import clsx from "clsx";
import React from "react";

interface ModalButtonProps {
  testId?: string;
  "data-testid"?: string;
  variant?: "default" | "text-like";
  onClick?: () => void;
  text: string;
  className: React.HTMLProps<HTMLButtonElement>["className"];
  icon?: React.ReactNode;
  type?: "button" | "submit";
  disabled?: boolean;
  intent?: string;
}

export function ModalButton({
  testId,
  "data-testid": dataTestId,
  variant = "default",
  onClick,
  text,
  className,
  icon,
  type = "button",
  disabled,
  intent,
}: ModalButtonProps) {
  return (
    <button
      data-testid={dataTestId || testId}
      type={type === "submit" ? "submit" : "button"}
      disabled={disabled}
      onClick={onClick}
      className={clsx(
        variant === "default" && "text-sm font-[500] py-[10px] rounded",
        variant === "text-like" && "text-xs leading-4 font-normal",
        icon && "flex items-center justify-center gap-2",
        disabled && "opacity-50 cursor-not-allowed",
        className,
      )}
      name={intent && "intent"}
      value={intent}
    >
      {icon}
      {text}
    </button>
  );
}
