import { useFetcher } from "@remix-run/react";
import ModalButton from "../buttons/ModalButton";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import { CustomInput } from "../form/custom-input";
import { clientAction } from "#/routes/create-repository";
import { isGitHubErrorReponse } from "#/api/github";

interface PushToGitHubModalProps {
  token: string;
  onClose: () => void;
}

export function PushToGitHubModal({ token, onClose }: PushToGitHubModalProps) {
  const fetcher = useFetcher<typeof clientAction>();
  const actionData = fetcher.data;

  return (
    <ModalBody>
      <BaseModalTitle title="Push to GitHub" />
      <fetcher.Form
        method="POST"
        action="/create-repository"
        className="w-full flex flex-col gap-6"
      >
        {actionData && isGitHubErrorReponse(actionData) && (
          <div className="text-red-500 text-sm">{actionData.message}</div>
        )}
        <input type="text" hidden name="ghToken" defaultValue={token} />
        <CustomInput name="repositoryName" label="Repository Name" required />
        <CustomInput
          name="repositoryDescription"
          label="Repository Description"
        />
        <div className="w-full flex flex-col gap-2">
          <ModalButton
            type="submit"
            text="Create"
            disabled={fetcher.state === "submitting"}
            className="bg-[#4465DB] w-full"
          />
          <ModalButton
            text="Close"
            className="bg-[#737373] w-full"
            onClick={onClose}
          />
        </div>
      </fetcher.Form>
    </ModalBody>
  );
}
