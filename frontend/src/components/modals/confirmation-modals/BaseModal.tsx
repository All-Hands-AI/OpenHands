import React from "react";
import ModalButton from "#/components/buttons/ModalButton";
import ModalBody from "../ModalBody";

interface ButtonConfig {
  text: string;
  onClick: () => void;
  className: React.HTMLProps<HTMLButtonElement>["className"];
}

interface BaseModalTitleProps {
  title: React.ReactNode;
}

export function BaseModalTitle({ title }: BaseModalTitleProps) {
  return (
    <span className="text-xl leading-6 -tracking-[0.01em] font-semibold">
      {title}
    </span>
  );
}

interface BaseModalDescriptionProps {
  description: React.ReactNode;
}

export function BaseModalDescription({
  description,
}: BaseModalDescriptionProps) {
  return <span className="text-xs text-[#A3A3A3]">{description}</span>;
}

interface BaseModalProps {
  title: string;
  description: string;
  buttons: ButtonConfig[];
}

function BaseModal({ title, description, buttons }: BaseModalProps) {
  return (
    <ModalBody>
      <div className="flex flex-col gap-2 self-start">
        <BaseModalTitle title={title} />
        <BaseModalDescription description={description} />
      </div>

      <div className="flex flex-col gap-2 w-full">
        {buttons.map((button, index) => (
          <ModalButton
            key={index}
            onClick={button.onClick}
            text={button.text}
            className={button.className}
          />
        ))}
      </div>
    </ModalBody>
  );
}

export default BaseModal;
