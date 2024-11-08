import { useFetcher, useRouteLoaderData } from "@remix-run/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import FormFieldset from "../form/FormFieldset";
import { CustomInput } from "../form/custom-input";
import { clientLoader } from "#/routes/_oh";
import { clientAction as settingsClientAction } from "#/routes/settings";
import { clientAction as loginClientAction } from "#/routes/login";
import { AvailableLanguages } from "#/i18n";
import { I18nKey } from "#/i18n/declaration";

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
  const data = useRouteLoaderData<typeof clientLoader>("routes/_oh");
  const settingsFetcher = useFetcher<typeof settingsClientAction>({
    key: "settings",
  });
  const loginFetcher = useFetcher<typeof loginClientAction>({ key: "login" });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const language = formData.get("language")?.toString();
    const ghToken = formData.get("ghToken")?.toString();
    const analytics = formData.get("analytics")?.toString() === "on";

    const accountForm = new FormData();
    const loginForm = new FormData();

    accountForm.append("intent", "account");
    if (language) {
      const languageKey = AvailableLanguages.find(
        ({ label }) => label === language,
      )?.value;
      accountForm.append("language", languageKey ?? "en");
    }
    if (ghToken) loginForm.append("ghToken", ghToken);
    accountForm.append("analytics", analytics.toString());

    settingsFetcher.submit(accountForm, {
      method: "POST",
      action: "/settings",
    });
    loginFetcher.submit(loginForm, {
      method: "POST",
      action: "/login",
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
            defaultValue={data?.ghToken ?? ""}
          />
          {gitHubError && (
            <p className="text-danger text-xs">
              {t(I18nKey.ACCOUNT_SETTINGS_MODAL$GITHUB_TOKEN_INVALID)}
            </p>
          )}
          {data?.ghToken && !gitHubError && (
            <ModalButton
              variant="text-like"
              text={t(I18nKey.ACCOUNT_SETTINGS_MODAL$DISCONNECT)}
              onClick={() => {
                settingsFetcher.submit(
                  {},
                  { method: "POST", action: "/logout" },
                );
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
            disabled={
              settingsFetcher.state === "submitting" ||
              loginFetcher.state === "submitting"
            }
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
