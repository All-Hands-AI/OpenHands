import { Button } from "@heroui/react";
import React from "react";

export interface Action {
  action: () => void;
  isDisabled?: boolean;
  label: string;
  className?: string;
  closeAfterAction?: boolean;
}

interface FooterContentProps {
  actions: Action[];
  closeModal: () => void;
}

export function FooterContent({ actions, closeModal }: FooterContentProps) {
  return (
    <>
      {actions.map(
        ({ action, isDisabled, label, className, closeAfterAction }) => (
          <Button
            key={label}
            type="button"
            isDisabled={isDisabled}
            onPress={() => {
              action();
              if (closeAfterAction) closeModal();
            }}
            className={className}
          >
            {label}
          </Button>
        ),
      )}
    </>
  );
}
