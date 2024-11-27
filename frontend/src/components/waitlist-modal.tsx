import { ModalButton } from "./buttons/modal-button";
import { ModalBackdrop } from "./modals/modal-backdrop";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBody } from "./modals/modal-body";
import { JoinWaitlistAnchor } from "./join-waitlist-anchor";
import { WaitlistMessage } from "./waitlist-message";

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
