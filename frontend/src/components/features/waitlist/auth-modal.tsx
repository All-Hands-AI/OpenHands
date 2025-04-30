import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { TOSCheckbox } from "./tos-checkbox";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { BrandButton } from "../settings/brand-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import GitLabLogo from "#/assets/branding/gitlab-logo.svg?react";
import { useAuthUrl } from "#/hooks/use-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";

interface AuthModalProps {
  githubAuthUrl: string | null;
  appMode?: GetConfigResponse["APP_MODE"] | null;
}

export function AuthModal({ githubAuthUrl, appMode }: AuthModalProps) {
  const { t } = useTranslation();
  const [isTosAccepted, setIsTosAccepted] = React.useState(false);

  const gitlabAuthUrl = useAuthUrl({
    appMode: appMode || null,
    identityProvider: "gitlab",
  });

  const handleGitHubAuth = () => {
    if (githubAuthUrl) {
      handleCaptureConsent(true);
      window.location.href = githubAuthUrl;
    }
  };

  const handleGitLabAuth = () => {
    if (gitlabAuthUrl) {
      handleCaptureConsent(true);
      window.location.href = gitlabAuthUrl;
    }
  };

  return (
    <ModalBackdrop>
      <ModalBody className="border border-tertiary">
        <AllHandsLogo width={68} height={46} />
        <div className="flex flex-col gap-2 w-full items-center text-center">
          <h1 className="text-2xl font-bold">
            {t(I18nKey.AUTH$SIGN_IN_WITH_IDENTITY_PROVIDER)}
          </h1>
        </div>

        <TOSCheckbox onChange={() => setIsTosAccepted((prev) => !prev)} />

        <div className="flex flex-col gap-3 w-full">
          <BrandButton
            isDisabled={!isTosAccepted}
            type="button"
            variant="primary"
            onClick={handleGitHubAuth}
            className="w-full"
            startContent={<GitHubLogo width={20} height={20} />}
          >
            {t(I18nKey.GITHUB$CONNECT_TO_GITHUB)}
          </BrandButton>

          <BrandButton
            isDisabled={!isTosAccepted}
            type="button"
            variant="primary"
            onClick={handleGitLabAuth}
            className="w-full"
            startContent={<GitLabLogo width={20} height={20} />}
          >
            {t(I18nKey.GITLAB$CONNECT_TO_GITLAB)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
