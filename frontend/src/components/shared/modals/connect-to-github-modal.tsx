import { useTranslation } from "react-i18next";
import { ModalBody } from "./modal-body";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/base-modal";
import { I18nKey } from "#/i18n/declaration";
import { useAuth } from "#/context/auth-context";
import { ModalButton } from "../buttons/modal-button";
import { CustomInput } from "../custom-input";

interface ConnectToGitHubModalProps {
  onClose: () => void;
}

export function ConnectToGitHubModal({ onClose }: ConnectToGitHubModalProps) {
  const { gitHubToken, setGitHubToken } = useAuth();
  const { t } = useTranslation();

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const ghToken = formData.get("ghToken")?.toString();

    if (ghToken) setGitHubToken(ghToken);
    onClose();
  };

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
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-6">
        <CustomInput
          label="GitHub Token"
          name="ghToken"
          required
          type="password"
          defaultValue={gitHubToken ?? ""}
        />

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            testId="connect-to-github"
            type="submit"
            text={t(I18nKey.CONNECT_TO_GITHUB_MODAL$CONNECT)}
            className="bg-[#791B80] w-full"
          />
          <ModalButton
            onClick={onClose}
            text={t(I18nKey.CONNECT_TO_GITHUB_MODAL$CLOSE)}
            className="bg-[#737373] w-full"
          />
        </div>
      </form>
    </ModalBody>
  );
}
