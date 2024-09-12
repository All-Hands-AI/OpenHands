import { useFetcher } from "@remix-run/react";
import React from "react";
import ModalBody from "./ModalBody";
import { CustomInput } from "../form/custom-input";
import ModalButton from "../buttons/ModalButton";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import { clientAction } from "#/root";

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
      <BaseModalTitle title="Connect to GitHub" />
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
