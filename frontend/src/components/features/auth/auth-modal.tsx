import React from "react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { AuthMessage } from "./auth-message";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { TOSCheckbox } from "./tos-checkbox";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { BrandButton } from "../settings/brand-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";

interface AuthModalProps {
  ghTokenIsSet: boolean;
  githubAuthUrl: string | null;
}

export function AuthModal({ ghTokenIsSet, githubAuthUrl }: AuthModalProps) {
  const [isTosAccepted, setIsTosAccepted] = React.useState(false);

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
        <AuthMessage content={ghTokenIsSet ? "waitlist" : "sign-in"} />

        <TOSCheckbox onChange={() => setIsTosAccepted((prev) => !prev)} />

        {!ghTokenIsSet && (
          <BrandButton
            isDisabled={!isTosAccepted}
            type="button"
            variant="primary"
            onClick={handleGitHubAuth}
            className="w-full"
            startContent={<GitHubLogo width={20} height={20} />}
          >
            Connect to GitHub
          </BrandButton>
        )}
      </ModalBody>
    </ModalBackdrop>
  );
}
