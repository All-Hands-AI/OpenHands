import { useFetcher, useRouteLoaderData } from "@remix-run/react";
import React from "react";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import FormFieldset from "../form/FormFieldset";
import { CustomInput } from "../form/custom-input";
import { clientLoader } from "#/root";
import { clientAction } from "#/routes/Settings";

interface AccountSettingsModalProps {
  onClose: () => void;
  language: string;
}

function AccountSettingsModal({
  onClose,
  language,
}: AccountSettingsModalProps) {
  const data = useRouteLoaderData<typeof clientLoader>("root");
  const fetcher = useFetcher<typeof clientAction>();

  React.useEffect(() => {
    if (fetcher.data?.success) onClose();
  }, [fetcher.data]);

  return (
    <ModalBody>
      <fetcher.Form
        method="POST"
        action="/settings"
        className="flex flex-col w-full gap-6"
      >
        <div className="w-full flex flex-col gap-2">
          <BaseModalTitle title="Account Settings" />

          <FormFieldset
            id="language"
            label="Language"
            defaultSelectedKey={language}
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
            onClick={() => console.log("Disconnect GH")}
            className="text-danger self-start"
          />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            disabled={fetcher.state === "submitting"}
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
      </fetcher.Form>
    </ModalBody>
  );
}

export default AccountSettingsModal;
