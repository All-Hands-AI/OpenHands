import { useFetcher } from "@remix-run/react";
import ModalBody from "./ModalBody";
import { CustomInput } from "../form/custom-input";
import ModalButton from "../buttons/ModalButton";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import { clientAction } from "#/routes/login";

interface ConnectToGitHubModalProps {
  onClose: () => void;
}

export function ConnectToGitHubModal({ onClose }: ConnectToGitHubModalProps) {
  const ghToken = localStorage.getItem("ghToken");
  const fetcher = useFetcher<typeof clientAction>({ key: "login" });

  return (
    <ModalBody>
      <div className="flex flex-col gap-2 self-start">
        <BaseModalTitle title="Connect to GitHub" />
        <BaseModalDescription
          description={
            <span>
              Get your token{" "}
              <a
                href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
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
        action="/login"
        className="w-full flex flex-col gap-6"
        onSubmit={onClose}
      >
        <CustomInput
          label="GitHub Token"
          name="ghToken"
          required
          type="password"
          defaultValue={ghToken ?? ""}
        />

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            testId="connect-to-github"
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
