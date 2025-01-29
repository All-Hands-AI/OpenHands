import { useTranslation } from "react-i18next";
import { BaseModal } from "./base-modal/base-modal";
import { LoadingSpinner } from "../loading-spinner";
import { I18nKey } from "#/i18n/declaration";

interface ConnectionStatusModalProps {
  isOpen: boolean;
}

export function ConnectionStatusModal({ isOpen }: ConnectionStatusModalProps) {
  const { t } = useTranslation();

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={() => {}}
      showCloseButton={false}
      className="max-w-md"
    >
      <div className="flex flex-col items-center justify-center p-6 space-y-4">
        <LoadingSpinner className="w-8 h-8" />
        <p className="text-lg font-medium text-gray-700">
          {t(I18nKey.MODAL$UNSTABLE_CONNECTION)}
        </p>
      </div>
    </BaseModal>
  );
}
