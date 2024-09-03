import clsx from "clsx";
import React from "react";

interface ModalButtonProps {
  variant?: "default" | "text-like";
  onClick: () => void;
  text: string;
  className: React.HTMLProps<HTMLButtonElement>["className"];
  icon?: React.ReactNode;
}

function ModalButton({
  variant = "default",
  onClick,
  text,
  className,
  icon,
}: ModalButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        variant === "default" && "text-sm text-[500] py-[10px] rounded",
        variant === "text-like" && "text-xs leading-4 font-normal",
        icon && "flex items-center justify-center gap-2",
        className,
      )}
    >
      {icon}
      {text}
    </button>
  );
}

export default ModalButton;
