import React from "react";
import { ModalBackdrop } from "./modal-backdrop";

interface BaseModalProps {
  onClose: () => void;
  children: React.ReactNode;
}

export function BaseModal({ onClose, children }: BaseModalProps) {
  return <ModalBackdrop onClose={onClose}>{children}</ModalBackdrop>;
}
