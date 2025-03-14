import React from "react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { TOSCheckbox } from "./tos-checkbox";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { BrandButton } from "../settings/brand-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";

interface AuthModalProps {
  githubAuthUrl: string | null;
}

export function AuthModal({ githubAuthUrl }: AuthModalProps) {
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
        <div className="flex flex-col gap-2 w-full items-center text-center">
          <h1 className="text-2xl font-bold">Sign in with GitHub</h1>
        </div>

        <TOSCheckbox onChange={() => setIsTosAccepted((prev) => !prev)} />

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
      </ModalBody>
    </ModalBackdrop>
  );
}
