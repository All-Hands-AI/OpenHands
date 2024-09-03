import React from "react";
import ModalButton from "#/components/buttons/ModalButton";

interface ButtonConfig {
  text: string;
  onClick: () => void;
  className: React.HTMLProps<HTMLButtonElement>["className"];
}

interface BaseModalProps {
  title: string;
  description: string;
  buttons: ButtonConfig[];
}

function BaseModal({ title, description, buttons }: BaseModalProps) {
  return (
    <div className="flex flex-col gap-6 p-6 w-[384px] rounded-xl bg-root-primary">
      <div className="flex flex-col gap-2">
        <span className="text-xl leading-6 -tracking-[0.01em] font-semibold">
          {title}
        </span>
        <p className="text-xs text-[#A3A3A3]">{description}</p>
      </div>

      <div className="flex flex-col gap-2">
        {buttons.map((button, index) => (
          <ModalButton
            key={index}
            onClick={button.onClick}
            text={button.text}
            className={button.className}
          />
        ))}
      </div>
    </div>
  );
}

export default BaseModal;
