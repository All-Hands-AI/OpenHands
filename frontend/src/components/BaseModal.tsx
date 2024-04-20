import React from "react";
import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@nextui-org/react";

interface Action {
  action: () => void;
  label: string;
  className?: string;
  closeAfterAction?: boolean;
}

interface BaseModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  title: string;
  subtitle?: string;
  actions?: Action[];
  children?: React.ReactNode;
}

const BaseModal: React.FC<BaseModalProps> = ({
  isOpen,
  onOpenChange,
  title,
  subtitle,
  actions,
  children,
}) => (
  <Modal
    isOpen={isOpen}
    onOpenChange={onOpenChange}
    title={title}
    backdrop="blur"
    hideCloseButton
    size="sm"
    className="bg-neutral-900 rounded-large"
  >
    <ModalContent className="max-w-[24rem] p-[40px]">
      {(closeModal) => (
        <>
          <ModalHeader className="flex flex-col p-0">
            <h3>{title}</h3>
            {subtitle && (
              <span className="text-neutral-400 text-sm font-light">
                {subtitle}
              </span>
            )}
          </ModalHeader>

          <ModalBody className="px-0 py-[20px]">{children}</ModalBody>

          {actions && actions.length > 0 && (
            <ModalFooter className="flex-col flex justify-start p-0">
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
            </ModalFooter>
          )}
        </>
      )}
    </ModalContent>
  </Modal>
);

BaseModal.defaultProps = {
  subtitle: undefined,
  actions: [],
  children: null,
};

export default BaseModal;
