import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@nextui-org/react";
import React from "react";
import { Action, FooterContent } from "./FooterContent";
import { HeaderContent } from "./HeaderContent";

interface BaseModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  title: string;
  isDismissable?: boolean;
  subtitle?: string;
  actions?: Action[];
  children?: React.ReactNode;
}

function BaseModal({
  isOpen,
  onOpenChange,
  title,
  isDismissable = true,
  subtitle,
  actions,
  children,
}: BaseModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title={title}
      isDismissable={isDismissable}
      backdrop="blur"
      hideCloseButton
      size="sm"
      className="bg-neutral-900 rounded-lg"
    >
      <ModalContent className="max-w-[24rem] p-[40px]">
        {(closeModal) => (
          <>
            <ModalHeader className="flex flex-col p-0">
              <HeaderContent title={title} subtitle={subtitle} />
            </ModalHeader>

            <ModalBody className="px-0 py-[20px]">{children}</ModalBody>

            {actions && actions.length > 0 && (
              <ModalFooter className="flex-col flex justify-start p-0">
                <FooterContent actions={actions} closeModal={closeModal} />
              </ModalFooter>
            )}
          </>
        )}
      </ModalContent>
    </Modal>
  );
}

BaseModal.defaultProps = {
  isDismissable: true,
  subtitle: undefined,
  actions: [],
  children: null,
};

export default BaseModal;
