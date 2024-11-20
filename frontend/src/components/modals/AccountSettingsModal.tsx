import { useFetcher } from "@remix-run/react";
import React from "react";
import { useTranslation } from "react-i18next";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import FormFieldset from "../form/FormFieldset";
import { CustomInput } from "../form/custom-input";
import { clientAction as settingsClientAction } from "#/routes/settings";
import { AvailableLanguages } from "#/i18n";
import { I18nKey } from "#/i18n/declaration";
import { getGitHubToken, setGitHubToken } from "#/services/auth";
import { logoutCleanup } from "#/utils/logout-cleanup";

interface AccountSettingsModalProps {
  onClose: () => void;
  selectedLanguage: string;
  gitHubError: boolean;
  analyticsConsent: string | null;
}

function AccountSettingsModal({
  onClose,
  selectedLanguage,
  gitHubError,
  analyticsConsent,
}: AccountSettingsModalProps) {
  const { t } = useTranslation();
  const settingsFetcher = useFetcher<typeof settingsClientAction>({
    key: "settings",
  });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const language = formData.get("language")?.toString();
    const ghToken = formData.get("ghToken")?.toString();
    const analytics = formData.get("analytics")?.toString() === "on";

    const accountForm = new FormData();

    accountForm.append("intent", "account");
    if (language) {
      const languageKey = AvailableLanguages.find(
        ({ label }) => label === language,
      )?.value;
      accountForm.append("language", languageKey ?? "en");
    }
    if (ghToken) setGitHubToken(ghToken);
    accountForm.append("analytics", analytics.toString());

    settingsFetcher.submit(accountForm, {
      method: "POST",
      action: "/settings",
    });

    onClose();
  };

  return (
    <ModalBody>
      <form className="flex flex-col w-full gap-6" onSubmit={handleSubmit}>
        <div className="w-full flex flex-col gap-2">
          <BaseModalTitle title="Account Settings" />

          <FormFieldset
            id="language"
            label="Language"
            defaultSelectedKey={selectedLanguage}
            isClearable={false}
            items={AvailableLanguages.map(({ label, value: key }) => ({
              key,
              value: label,
            }))}
          />

          <CustomInput
            name="ghToken"
            label="GitHub Token"
            type="password"
            defaultValue={getGitHubToken() ?? ""}
          />
          <BaseModalDescription>
            {t(I18nKey.CONNECT_TO_GITHUB_MODAL$GET_YOUR_TOKEN)}{" "}
            <a
              href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
              target="_blank"
              rel="noreferrer noopener"
              className="text-[#791B80] underline"
            >
              {t(I18nKey.CONNECT_TO_GITHUB_MODAL$HERE)}
            </a>
          </BaseModalDescription>
          {gitHubError && (
            <p className="text-danger text-xs">
              {t(I18nKey.ACCOUNT_SETTINGS_MODAL$GITHUB_TOKEN_INVALID)}
            </p>
          )}
          {getGitHubToken() && !gitHubError && (
            <ModalButton
              variant="text-like"
              text={t(I18nKey.ACCOUNT_SETTINGS_MODAL$DISCONNECT)}
              onClick={() => {
                logoutCleanup();
                onClose();
              }}
              className="text-danger self-start"
            />
          )}
        </div>

        <label className="flex gap-2 items-center self-start">
          <input
            name="analytics"
            type="checkbox"
            defaultChecked={analyticsConsent === "true"}
          />
          Enable analytics
        </label>

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            disabled={settingsFetcher.state === "submitting"}
            type="submit"
            intent="account"
            text={t(I18nKey.ACCOUNT_SETTINGS_MODAL$SAVE)}
            className="bg-[#4465DB]"
          />
          <ModalButton
            text={t(I18nKey.ACCOUNT_SETTINGS_MODAL$CLOSE)}
            onClick={onClose}
            className="bg-[#737373]"
          />
        </div>
      </form>
    </ModalBody>
  );
}

export default AccountSettingsModal;
