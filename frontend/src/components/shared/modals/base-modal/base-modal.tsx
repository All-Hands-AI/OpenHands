import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/react";
import React from "react";
import { Action, FooterContent } from "./footer-content";
import { HeaderContent } from "./header-content";

interface BaseModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  title: string;
  contentClassName?: string;
  bodyClassName?: string;
  isDismissable?: boolean;
  subtitle?: string;
  actions?: Action[];
  children?: React.ReactNode;
  testID?: string;
}

export function BaseModal({
  isOpen,
  onOpenChange,
  title,
  contentClassName = "max-w-[30rem] p-[40px]",
  bodyClassName = "px-0 py-[20px]",
  isDismissable = true,
  subtitle = undefined,
  actions = [],
  children = null,
  testID,
}: BaseModalProps) {
  return (
    <Modal
      data-testid={testID}
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      isDismissable={isDismissable}
      backdrop="blur"
      hideCloseButton
      size="sm"
      className="bg-base-secondary rounded-lg"
    >
      <ModalContent className={contentClassName}>
        {(closeModal) => (
          <>
            {title && (
              <ModalHeader className="flex flex-col p-0">
                <HeaderContent maintitle={title} subtitle={subtitle} />
              </ModalHeader>
            )}

            <ModalBody className={bodyClassName}>{children}</ModalBody>

            {actions && actions.length > 0 && (
              <ModalFooter className="flex-row flex justify-start p-0">
                <FooterContent actions={actions} closeModal={closeModal} />
              </ModalFooter>
            )}
          </>
        )}
      </ModalContent>
    </Modal>
  );
}
