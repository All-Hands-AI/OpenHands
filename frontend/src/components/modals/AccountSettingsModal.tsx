import { useFetcher, useRouteLoaderData } from "@remix-run/react";
import React from "react";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import FormFieldset from "../form/FormFieldset";
import { CustomInput } from "../form/custom-input";
import { clientLoader } from "#/root";
import { clientAction as settingsClientAction } from "#/routes/Settings";
import { clientAction as loginClientAction } from "#/routes/login";

interface AccountSettingsModalProps {
  onClose: () => void;
  selectedLanguage: string;
}

function AccountSettingsModal({
  onClose,
  selectedLanguage,
}: AccountSettingsModalProps) {
  const data = useRouteLoaderData<typeof clientLoader>("root");
  const settingsFetcher = useFetcher<typeof settingsClientAction>({
    key: "settings",
  });
  const loginFetcher = useFetcher<typeof loginClientAction>({ key: "login" });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const language = formData.get("language")?.toString();
    const ghToken = formData.get("ghToken")?.toString();

    const accountForm = new FormData();
    const loginForm = new FormData();

    accountForm.append("intent", "account");
    if (language) accountForm.append("language", language);
    if (ghToken) loginForm.append("ghToken", ghToken);

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
            items={[
              { key: "en", value: "English" },
              { key: "es", value: "Spanish" },
              { key: "fr", value: "French" },
            ]}
          />

          <CustomInput
            name="ghToken"
            label="GitHub Token"
            type="password"
            defaultValue={data?.ghToken ?? ""}
          />
          <ModalButton
            variant="text-like"
            text="Disconnect"
            onClick={() => {
              settingsFetcher.submit({}, { method: "POST", action: "/logout" });
              onClose();
            }}
            className="text-danger self-start"
          />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            disabled={
              settingsFetcher.state === "submitting" ||
              loginFetcher.state === "submitting"
            }
            type="submit"
            intent="account"
            text="Save"
            className="bg-[#4465DB]"
          />
          <ModalButton
            text="Close"
            onClick={onClose}
            className="bg-[#737373]"
          />
        </div>
      </form>
    </ModalBody>
  );
}

export default AccountSettingsModal;
