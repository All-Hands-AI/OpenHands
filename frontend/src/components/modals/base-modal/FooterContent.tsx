import { Button } from "@nextui-org/react";
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
    <div className="flex justify-end space-x-2">
      {actions.map(
        ({ action, isDisabled, label, className, closeAfterAction }) => (
          <Button
            key={label}
            type="button"
            isDisabled={isDisabled}
            onClick={() => {
              action();
              if (closeAfterAction) closeModal();
            }}
            className={`px-4 py-2 rounded text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed ${className}`}
          >
            {label}
          </Button>
        ),
      )}
    </div>
  );
}
