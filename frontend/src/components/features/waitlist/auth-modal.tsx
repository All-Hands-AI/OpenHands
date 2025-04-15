import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { BrandButton } from "../settings/brand-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";

interface AuthModalProps {
  githubAuthUrl: string | null;
}

export function AuthModal({ githubAuthUrl }: AuthModalProps) {
  const { t } = useTranslation();

  const handleGitHubAuth = () => {
    if (githubAuthUrl) {
      handleCaptureConsent(true);
      window.location.href = githubAuthUrl;
    }
  };

  return (
    <ModalBackdrop>
      <ModalBody className="border border-tertiary">
        <AllHandsLogo width={68} height={46} />
        <div className="flex flex-col gap-2 w-full items-center text-center">
          <h1 className="text-2xl font-bold">
            {t(I18nKey.AUTH$SIGN_IN_WITH_GITHUB)}
          </h1>
        </div>

        <div className="text-sm text-muted-foreground mb-2 text-center">
          By signing in, you agree to our{" "}
          <a
            href="https://www.all-hands.dev/tos"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 text-blue-500 hover:text-blue-700"
          >
            {t(I18nKey.TOS$TERMS)}
          </a>
        </div>

        <BrandButton
          type="button"
          variant="primary"
          onClick={handleGitHubAuth}
          className="w-full"
          startContent={<GitHubLogo width={20} height={20} />}
        >
          {t(I18nKey.GITHUB$CONNECT_TO_GITHUB)}
        </BrandButton>
      </ModalBody>
    </ModalBackdrop>
  );
}
