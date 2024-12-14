import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { FeedbackForm } from "./feedback-form";

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
  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody>
        <BaseModalTitle title="Feedback" />
        <BaseModalDescription description="To help us improve, we collect feedback from your interactions to improve our prompts. By submitting this form, you consent to us collecting this data." />
        <FeedbackForm onClose={onClose} polarity={polarity} />
      </ModalBody>
    </ModalBackdrop>
  );
}
