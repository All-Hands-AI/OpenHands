import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useCurrentSettings } from "#/context/settings-context";

export function TOSModal() {
  const { t } = useTranslation();
  const { saveUserSettings } = useCurrentSettings();

  const handleAcceptTOS = () => {
    saveUserSettings({ ACCEPT_TOS: true });
  };

  return (
    <ModalBackdrop>
      <div
        data-testid="tos-modal"
        className="bg-base-secondary min-w-[384px] p-6 rounded-xl flex flex-col gap-4 border border-tertiary"
      >
        <span className="text-xl leading-6 font-semibold -tracking-[0.01em]">
          {t(I18nKey.TOS$TITLE)}
        </span>
        <p className="text-sm text-[#A3A3A3]">
          {t(I18nKey.TOS$DESCRIPTION)}{" "}
          <a
            href="https://www.all-hands.dev/tos"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 text-white"
          >
            {t(I18nKey.TOS$READ_MORE)}
          </a>
        </p>
        <BrandButton
          testId="accept-tos-button"
          type="button"
          variant="primary"
          onClick={handleAcceptTOS}
        >
          {t(I18nKey.TOS$ACCEPT)}
        </BrandButton>
      </div>
    </ModalBackdrop>
  );
}
