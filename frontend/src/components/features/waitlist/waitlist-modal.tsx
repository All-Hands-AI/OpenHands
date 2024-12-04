import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { JoinWaitlistAnchor } from "./join-waitlist-anchor";
import { WaitlistMessage } from "./waitlist-message";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { ModalBody } from "#/components/shared/modals/modal-body";

interface WaitlistModalProps {
  ghToken: string | null;
  githubAuthUrl: string | null;
}

export function WaitlistModal({ ghToken, githubAuthUrl }: WaitlistModalProps) {
  return (
    <ModalBackdrop>
      <ModalBody>
        <AllHandsLogo width={68} height={46} />
        <WaitlistMessage content={ghToken ? "waitlist" : "sign-in"} />

        {!ghToken && (
          <ModalButton
            text="Connect to GitHub"
            icon={<GitHubLogo width={20} height={20} />}
            className="bg-[#791B80] w-full"
            onClick={() => {
              if (githubAuthUrl) {
                window.location.href = githubAuthUrl;
              }
            }}
          />
        )}
        {ghToken && <JoinWaitlistAnchor />}
      </ModalBody>
    </ModalBackdrop>
  );
}
