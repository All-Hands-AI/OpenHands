import ModalButton from "./buttons/ModalButton";
import { ModalBackdrop } from "./modals/modal-backdrop";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import ModalBody from "./modals/ModalBody";

interface WaitlistModalProps {
  ghToken: string | null;
  githubAuthUrl: string | null;
}

export function WaitlistModal({ ghToken, githubAuthUrl }: WaitlistModalProps) {
  return (
    <ModalBackdrop>
      <ModalBody>
        <AllHandsLogo width={68} height={46} />
        <div className="flex flex-col gap-2 w-full items-center text-center">
          <h1 className="text-2xl font-bold">
            {ghToken ? "GitHub Token Expired" : "Sign in with GitHub"}
          </h1>
          {!ghToken && (
            <p>
              or{" "}
              <a
                href="https://www.all-hands.dev/join-waitlist"
                target="_blank"
                rel="noreferrer noopener"
                className="text-blue-500 hover:underline underline-offset-2"
              >
                join the waitlist
              </a>{" "}
              if you haven&apos;t already
            </p>
          )}
          {ghToken && (
            <p className="text-sm">
              Your GitHub token has expired. Please click below to reconnect your GitHub account.
            </p>
          )}
        </div>

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
        {ghToken && (
          <ModalButton
            text="Reconnect to GitHub"
            icon={<GitHubLogo width={20} height={20} />}
            className="bg-[#791B80] w-full"
            onClick={() => {
              if (githubAuthUrl) {
                window.location.href = githubAuthUrl;
              }
            }}
          />
        )}
      </ModalBody>
    </ModalBackdrop>
  );
}
