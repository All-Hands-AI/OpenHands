import { Button } from "@nextui-org/react";
import React from "react";

export interface Action {
  action: () => void;
  label: string;
  className?: string;
  closeAfterAction?: boolean;
}

interface FooterContentProps {
  actions: Action[];
  closeModal: () => void;
}

export const FooterContent: React.FC<FooterContentProps> = ({
  actions,
  closeModal,
}) => (
  <>
    {actions.map(({ action, label, className, closeAfterAction }) => (
      <Button
        key={label}
        type="button"
        onClick={() => {
          action();
          if (closeAfterAction) closeModal();
        }}
        className={className}
      >
        {label}
      </Button>
    ))}
  </>
);
