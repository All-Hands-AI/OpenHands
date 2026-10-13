import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import XMarkIcon from "#/icons/x-mark.svg?react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import {
  MODAL_MAX_WIDTH_VIEWPORT,
  modalWidthClassName,
} from "#/components/shared/modals/modal-body";
import { modalTitleLgMediumClassName } from "#/utils/modal-classes";
import { cn } from "#/utils/utils";

interface DeleteDraftConfirmationModalProps {
  draftName?: string | null;
  isOpen: boolean;
  isDeleting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteDraftConfirmationModal({
  draftName,
  isOpen,
  isDeleting = false,
  onConfirm,
  onCancel,
}: DeleteDraftConfirmationModalProps) {
  const { t } = useTranslation("openhands");
  const cancelButtonRef = React.useRef<HTMLButtonElement>(null);
  const previousActiveElement = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      previousActiveElement.current =
        document.activeElement as HTMLElement | null;
      cancelButtonRef.current?.focus();
    }
  }, [isOpen]);

  const handleClose = () => {
    onCancel();
    previousActiveElement.current?.focus();
  };

  if (!isOpen) return null;

  const title = t(I18nKey.AUTOMATION_SETUP$DELETE_DRAFT_TITLE);

  return (
    <ModalBackdrop onClose={handleClose} aria-label={title}>
      <div
        className={cn(
          "relative rounded-xl border border-border bg-surface p-6",
          modalWidthClassName("sm"),
          MODAL_MAX_WIDTH_VIEWPORT,
        )}
      >
        <button
          type="button"
          onClick={handleClose}
          className="absolute right-4 top-4 text-muted hover:text-foreground"
          aria-label={t(I18nKey.BUTTON$CLOSE)}
        >
          <XMarkIcon className="size-5" />
        </button>

        <h2 className={modalTitleLgMediumClassName}>{title}</h2>
        <p className="mt-2 text-sm text-muted">
          {t(I18nKey.AUTOMATION_SETUP$DELETE_DRAFT_MESSAGE, {
            name: draftName ?? t(I18nKey.AUTOMATIONS$UNTITLED_DRAFT),
          })}
        </p>

        <div className="mt-6 flex justify-end gap-3">
          <button
            ref={cancelButtonRef}
            type="button"
            onClick={handleClose}
            className="rounded-lg border border-border px-4 py-2 text-sm text-contrast hover:bg-surface-raised"
          >
            {t(I18nKey.AUTOMATIONS$CANCEL)}
          </button>
          <button
            type="button"
            data-testid="automation-setup-draft-delete-confirm"
            onClick={onConfirm}
            disabled={isDeleting}
            className="rounded-lg bg-danger px-4 py-2 text-sm text-white hover:bg-danger/80 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {t(I18nKey.AUTOMATION_SETUP$DELETE_DRAFT)}
          </button>
        </div>
      </div>
    </ModalBackdrop>
  );
}
