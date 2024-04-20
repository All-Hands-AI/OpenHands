import React from "react";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@nextui-org/react";

interface Action {
  action: () => void;
  label: string;
}

interface BaseModalProps {
  isOpen: boolean;
  title: string;
  subtitle?: string;
  actions?: Action[];
  children?: React.ReactNode;
}

const BaseModal: React.FC<BaseModalProps> = ({
  isOpen,
  title,
  subtitle,
  actions,
  children,
}) => (
  <Modal isOpen={isOpen} title={title} backdrop="blur" hideCloseButton>
    <ModalContent>
      <ModalHeader>
        {title}
        {subtitle && <span>{subtitle}</span>}
      </ModalHeader>

      <ModalContent>{children}</ModalContent>

      <ModalFooter>
        {actions?.map(({ action, label }) => (
          <button key={label} type="button" onClick={action}>
            {label}
          </button>
        ))}
      </ModalFooter>
    </ModalContent>
  </Modal>
);

BaseModal.defaultProps = {
  subtitle: undefined,
  actions: [],
  children: null,
};

export default BaseModal;
