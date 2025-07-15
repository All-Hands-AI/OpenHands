import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import GitLabLogo from "#/assets/branding/gitlab-logo.svg?react";
import BitbucketLogo from "#/assets/branding/bitbucket-logo.svg?react";
import { useAuthUrl } from "#/hooks/use-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";

interface AuthModalProps {
  githubAuthUrl: string | null;
  appMode?: GetConfigResponse["APP_MODE"] | null;
}

export function AuthModal({ githubAuthUrl, appMode }: AuthModalProps) {
  const { t } = useTranslation();

  const gitlabAuthUrl = useAuthUrl({
    appMode: appMode || null,
    identityProvider: "gitlab",
  });

  const bitbucketAuthUrl = useAuthUrl({
    appMode: appMode || null,
    identityProvider: "bitbucket",
  });

  const handleGitHubAuth = () => {
    if (githubAuthUrl) {
      // Always start the OIDC flow, let the backend handle TOS check
      window.location.href = githubAuthUrl;
    }
  };

  const handleGitLabAuth = () => {
    if (gitlabAuthUrl) {
      // Always start the OIDC flow, let the backend handle TOS check
      window.location.href = gitlabAuthUrl;
    }
  };

  const handleBitbucketAuth = () => {
    if (bitbucketAuthUrl) {
      // Always start the OIDC flow, let the backend handle TOS check
      window.location.href = bitbucketAuthUrl;
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

        <div className="flex flex-col gap-3 w-full">
          <BrandButton
            type="button"
            variant="primary"
            onClick={handleGitHubAuth}
            className="w-full"
            startContent={<GitHubLogo width={20} height={20} />}
          >
            {t(I18nKey.GITHUB$CONNECT_TO_GITHUB)}
          </BrandButton>

          <BrandButton
            type="button"
            variant="primary"
            onClick={handleGitLabAuth}
            className="w-full"
            startContent={<GitLabLogo width={20} height={20} />}
          >
            {t(I18nKey.GITLAB$CONNECT_TO_GITLAB)}
          </BrandButton>

          <BrandButton
            type="button"
            variant="primary"
            onClick={handleBitbucketAuth}
            className="w-full"
            startContent={<BitbucketLogo width={20} height={20} />}
          >
            {t(I18nKey.BITBUCKET$CONNECT_TO_BITBUCKET)}
          </BrandButton>
        </div>

        <p
          className="mt-4 text-xs text-center text-muted-foreground"
          data-testid="auth-modal-terms-of-service"
        >
          {t(I18nKey.AUTH$BY_SIGNING_UP_YOU_AGREE_TO_OUR)}{" "}
          <a
            href="https://www.all-hands.dev/tos"
            target="_blank"
            className="underline hover:text-primary"
            rel="noopener noreferrer"
          >
            {t(I18nKey.COMMON$TERMS_OF_SERVICE)}
          </a>{" "}
          {t(I18nKey.COMMON$AND)}{" "}
          <a
            href="https://www.all-hands.dev/privacy"
            target="_blank"
            className="underline hover:text-primary"
            rel="noopener noreferrer"
          >
            {t(I18nKey.COMMON$PRIVACY_POLICY)}
          </a>
          .
        </p>
      </ModalBody>
    </ModalBackdrop>
  );
}
