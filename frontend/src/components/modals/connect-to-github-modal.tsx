import { useFetcher } from "@remix-run/react";
import React from "react";
import ModalBody from "./ModalBody";
import { CustomInput } from "../form/custom-input";
import ModalButton from "../buttons/ModalButton";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import { clientAction } from "#/root";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";

interface ConnectToGitHubModalProps {
  onClose: () => void;
}

export function ConnectToGitHubModal({ onClose }: ConnectToGitHubModalProps) {
  const fetcher = useFetcher<typeof clientAction>();

  React.useEffect(() => {
    if (fetcher.data?.success) onClose();
  }, [fetcher.data]);

  return (
    <ModalBody>
      <div className="flex flex-col gap-2 self-start">
        <BaseModalTitle title="Connect to GitHub" />
        <BaseModalDescription
          description={
            <span>
              Get your token{" "}
              <a
                href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user"
                target="_blank"
                rel="noreferrer noopener"
                className="text-[#791B80] underline"
              >
                here
              </a>
            </span>
          }
        />
      </div>
      <fetcher.Form
        method="POST"
        action="/"
        className="w-full flex flex-col gap-6"
      >
        <CustomInput label="GitHub Token" name="ghToken" required />

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            type="submit"
            text="Connect"
            disabled={fetcher.state === "submitting"}
            className="bg-[#791B80] w-full"
          />
          <ModalButton
            onClick={onClose}
            text="Close"
            className="bg-[#737373] w-full"
          />
        </div>
      </fetcher.Form>
    </ModalBody>
  );
}
