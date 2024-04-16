import React from "react";
import {
  ModalProps,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@nextui-org/react";

interface ODModalProps extends Omit<ModalProps, "children"> {
  title?: string;
  subtitle?: string;
  primaryAction?: React.ReactNode;
  secondaryAction?: React.ReactNode;
  children: React.ReactNode;
  isOpen: boolean;
  onClose: () => void;
  size: "sm" | "md";
}

function ODModal(props: ODModalProps): React.ReactElement {
  const {
    children,
    title,
    subtitle,
    primaryAction,
    secondaryAction,
    size,
    ...modalProps
  } = props;

  return (
    <Modal
      className="bg-neutral-900 rounded-large"
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...modalProps}
    >
      <ModalContent
        className={`${size === "sm" ? "max-w-[24rem]" : "max-w-[52rem]"} p-[40px]`}
      >
        <ModalHeader className="flex flex-col p-0">
          {title && <h3>{title}</h3>}
          {subtitle && (
            <span className="text-neutral-400 text-sm font-light">
              {subtitle}
            </span>
          )}
        </ModalHeader>
        <ModalBody className="px-0 py-[20px]">{children}</ModalBody>
        {(primaryAction || secondaryAction) && (
          <ModalFooter
            className={`${size === "sm" ? "flex-col" : "flex-row"} flex justify-start p-0`}
          >
            {primaryAction}
            {secondaryAction}
          </ModalFooter>
        )}
      </ModalContent>
    </Modal>
  );
}

ODModal.defaultProps = {
  title: "",
  subtitle: "",
  primaryAction: null,
  secondaryAction: null,
};

export default ODModal;
