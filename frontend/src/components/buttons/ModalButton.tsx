import clsx from "clsx";
import React from "react";

interface ModalButtonProps {
  onClick: () => void;
  text: string;
  className: React.HTMLProps<HTMLButtonElement>["className"];
}

function ModalButton({ onClick, text, className }: ModalButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx("text-sm text-[500] py-[10px] rounded", className)}
    >
      {text}
    </button>
  );
}

export default ModalButton;
