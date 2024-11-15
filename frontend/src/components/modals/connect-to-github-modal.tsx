import { useFetcher, useRouteLoaderData } from "@remix-run/react";
import { useTranslation } from "react-i18next";
import ModalBody from "./ModalBody";
import { CustomInput } from "../form/custom-input";
import ModalButton from "../buttons/ModalButton";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import { clientLoader } from "#/routes/_oh";
import { clientAction } from "#/routes/login";
import { I18nKey } from "#/i18n/declaration";

interface ConnectToGitHubModalProps {
  onClose: () => void;
}

export function ConnectToGitHubModal({ onClose }: ConnectToGitHubModalProps) {
  const data = useRouteLoaderData<typeof clientLoader>("routes/_oh");
  const fetcher = useFetcher<typeof clientAction>({ key: "login" });
  const { t } = useTranslation();

  return (
    <ModalBody>
      <div className="flex flex-col gap-2 self-start">
        <BaseModalTitle title="Connect to GitHub" />
        <BaseModalDescription
          description={
            <span>
              {t(I18nKey.CONNECT_TO_GITHUB_MODAL$GET_YOUR_TOKEN)}{" "}
              <a
                href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
                target="_blank"
                rel="noreferrer noopener"
                className="text-[#791B80] underline"
              >
                {t(I18nKey.CONNECT_TO_GITHUB_MODAL$HERE)}
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
          defaultValue={data?.ghToken ?? ""}
        />

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            testId="connect-to-github"
            type="submit"
            text={t(I18nKey.CONNECT_TO_GITHUB_MODAL$CONNECT)}
            disabled={fetcher.state === "submitting"}
            className="bg-[#791B80] w-full"
          />
          <ModalButton
            onClick={onClose}
            text={t(I18nKey.CONNECT_TO_GITHUB_MODAL$CLOSE)}
            className="bg-[#737373] w-full"
          />
        </div>
      </fetcher.Form>
    </ModalBody>
  );
}
