import React from "react";
import { useTranslation } from "react-i18next";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { I18nKey } from "#/i18n/declaration";

export function ReauthModal() {
  const { t } = useTranslation();

  return (
    <ModalBackdrop>
      <ModalBody className="border border-tertiary">
        <div className="flex flex-col items-center justify-center p-8">
          <p className="text-lg font-medium text-center">
            {t(I18nKey.AUTH$LOGGING_BACK_IN)}
          </p>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
