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
            {ghToken ? "Just a little longer!" : "Sign in with GitHub"}
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
              Thanks for your patience! We&apos;re accepting new members
              progressively. If you haven&apos;t joined the waitlist yet,
              now&apos;s the time!
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
          <a
            href="https://www.all-hands.dev/join-waitlist"
            target="_blank"
            rel="noreferrer"
            className="rounded bg-[#FFE165] text-black text-sm font-bold py-[10px] w-full text-center hover:opacity-80"
          >
            Join Waitlist
          </a>
        )}
      </ModalBody>
    </ModalBackdrop>
  );
}
