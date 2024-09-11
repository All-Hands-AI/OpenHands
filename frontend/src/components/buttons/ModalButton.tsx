import clsx from "clsx";
import React from "react";

interface ModalButtonProps {
  variant?: "default" | "text-like";
  onClick?: () => void;
  text: string;
  className: React.HTMLProps<HTMLButtonElement>["className"];
  icon?: React.ReactNode;
  type?: "button" | "submit";
  disabled?: boolean;
}

function ModalButton({
  variant = "default",
  onClick,
  text,
  className,
  icon,
  type = "button",
  disabled,
}: ModalButtonProps) {
  return (
    <button
      type={type === "submit" ? "submit" : "button"}
      disabled={disabled}
      onClick={onClick}
      className={clsx(
        variant === "default" && "text-sm text-[500] py-[10px] rounded",
        variant === "text-like" && "text-xs leading-4 font-normal",
        icon && "flex items-center justify-center gap-2",
        disabled && "opacity-50 cursor-not-allowed",
        className,
      )}
    >
      {icon}
      {text}
    </button>
  );
}

export default ModalButton;
