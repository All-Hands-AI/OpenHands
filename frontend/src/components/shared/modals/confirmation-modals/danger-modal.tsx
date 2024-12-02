import { BaseModal } from "./base-modal";

interface DangerModalProps {
  title: string;
  description: string;

  buttons: {
    danger: { text: string; onClick: () => void };
    cancel: { text: string; onClick: () => void };
  };
}

export function DangerModal({ title, description, buttons }: DangerModalProps) {
  return (
    <BaseModal
      title={title}
      description={description}
      buttons={[
        {
          text: buttons.danger.text,
          onClick: buttons.danger.onClick,
          className: "bg-danger",
        },
        {
          text: buttons.cancel.text,
          onClick: buttons.cancel.onClick,
          className: "bg-neutral-500",
        },
      ]}
    />
  );
}
