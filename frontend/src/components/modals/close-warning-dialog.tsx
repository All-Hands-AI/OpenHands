import { useTranslation } from "react-i18next";
import { Dialog } from "@headlessui/react";

interface CloseWarningDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function CloseWarningDialog({
  isOpen,
  onClose,
  onConfirm,
}: CloseWarningDialogProps) {
  const { t } = useTranslation();

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      className="relative z-50"
    >
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-sm rounded bg-white p-6">
          <Dialog.Title className="text-lg font-medium leading-6 text-gray-900">
            {t("CLOSE_WARNING$DIALOG_TITLE")}
          </Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-gray-500">
            {t("CLOSE_WARNING$DIALOG_MESSAGE")}
          </Dialog.Description>

          <div className="mt-4 flex justify-end space-x-2">
            <button
              type="button"
              className="inline-flex justify-center rounded-md border border-transparent bg-gray-100 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2"
              onClick={onClose}
            >
              {t("CLOSE_WARNING$DIALOG_CANCEL")}
            </button>
            <button
              type="button"
              className="inline-flex justify-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
              onClick={onConfirm}
            >
              {t("CLOSE_WARNING$DIALOG_CONFIRM")}
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
