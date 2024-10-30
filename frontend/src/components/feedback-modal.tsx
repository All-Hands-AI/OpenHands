import React from "react";
import hotToast, { toast } from "react-hot-toast";
import { useFetcher } from "@remix-run/react";
import { FeedbackForm } from "./feedback-form";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "./modals/confirmation-modals/BaseModal";
import { ModalBackdrop } from "./modals/modal-backdrop";
import ModalBody from "./modals/ModalBody";
import { clientAction } from "#/routes/submit-feedback";

interface FeedbackModalProps {
  onSubmit: (permissions: "private" | "public", email: string) => void;
  onClose: () => void;
  isOpen: boolean;
  isSubmitting?: boolean;
}

export function FeedbackModal({
  onSubmit,
  onClose,
  isOpen,
  isSubmitting,
}: FeedbackModalProps) {
  const fetcher = useFetcher<typeof clientAction>({ key: "feedback" });
  const isInitialRender = React.useRef(true);

  const copiedToClipboardToast = () => {
    hotToast("Password copied to clipboard", {
      icon: "📋",
      position: "bottom-right",
    });
  };

  const onPressToast = (password: string) => {
    navigator.clipboard.writeText(password);
    copiedToClipboardToast();
  };

  const shareFeedbackToast = (
    message: string,
    link: string,
    password: string,
  ) => {
    hotToast(
      <div className="flex flex-col gap-1">
        <span>{message}</span>
        <a
          data-testid="toast-share-url"
          className="text-blue-500 underline"
          onClick={() => onPressToast(password)}
          href={link}
          target="_blank"
          rel="noreferrer"
        >
          Go to shared feedback
        </a>
        <span onClick={() => onPressToast(password)} className="cursor-pointer">
          Password: {password} <span className="text-gray-500">(copy)</span>
        </span>
      </div>,
      { duration: 10000 },
    );
  };

  React.useEffect(() => {
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }

    // Handle feedback submission
    if (fetcher.state === "idle" && fetcher.data) {
      if (!fetcher.data.success) {
        toast.error("Error submitting feedback");
      } else if (fetcher.data.data) {
        const { data } = fetcher.data;
        const { message, link, password } = data;
        shareFeedbackToast(message, link, password);
      }

      onClose();
    }
  }, [fetcher.state, fetcher.data?.success]);

  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody>
        <BaseModalTitle title="Feedback" />
        <BaseModalDescription description="To help us improve, we collect feedback from your interactions to improve our prompts. By submitting this form, you consent to us collecting this data." />
        <FeedbackForm
          onSubmit={onSubmit}
          onClose={onClose}
          isSubmitting={isSubmitting}
        />
      </ModalBody>
    </ModalBackdrop>
  );
}
