import React from "react";
import hotToast, { toast } from "react-hot-toast";
import { FeedbackForm } from "./feedback-form";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "./modals/confirmation-modals/BaseModal";
import { ModalBackdrop } from "./modals/modal-backdrop";
import ModalBody from "./modals/ModalBody";
import { clientAction } from "#/routes/submit-feedback";

interface FeedbackModalProps {
  onClose: () => void;
  isOpen: boolean;
  polarity: "positive" | "negative";
}

export function FeedbackModal({
  onClose,
  isOpen,
  polarity,
}: FeedbackModalProps) {
  const copiedToClipboardToast = () => {
    hotToast("Password copied to clipboard", {
      icon: "📋",
      position: "bottom-right",
    });
  };

  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody>
        <BaseModalTitle title="Feedback" />
        <BaseModalDescription description="To help us improve, we collect feedback from your interactions to improve our prompts. By submitting this form, you consent to us collecting this data." />
        <FeedbackForm
          onClose={onClose}
          polarity={polarity}
        />
      </ModalBody>
    </ModalBackdrop>
  );
}
