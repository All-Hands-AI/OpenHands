import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
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
  const { t } = useTranslation();
  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody className="border border-tertiary">
        <BaseModalTitle title={t(I18nKey.FEEDBACK$TITLE)} />
        <BaseModalDescription description={t(I18nKey.FEEDBACK$DESCRIPTION)} />
        <FeedbackForm onClose={onClose} polarity={polarity} />
      </ModalBody>
    </ModalBackdrop>
  );
}
