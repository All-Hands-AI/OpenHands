import React from "react";
import clsx from "clsx";

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
          <button
            key={index}
            type="button"
            onClick={button.onClick}
            className={clsx(
              "text-sm text-[500] py-[10px] rounded",
              button.className,
            )}
          >
            {button.text}
          </button>
        ))}
      </div>
    </div>
  );
}

export default BaseModal;
