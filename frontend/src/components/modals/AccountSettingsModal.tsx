import { useFetcher } from "@remix-run/react";
import React from "react";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import FormFieldset from "../form/FormFieldset";

interface AccountSettingsModalProps {
  onClose: () => void;
  language: string;
}

function AccountSettingsModal({
  onClose,
  language,
}: AccountSettingsModalProps) {
  const fetcher = useFetcher();
  const formRef = React.useRef<HTMLFormElement>(null);

  return (
    <ModalBody>
      <div className="w-full flex flex-col gap-2">
        <BaseModalTitle title="Account Settings" />
        <fetcher.Form ref={formRef} method="POST" action="/settings">
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
        </fetcher.Form>
      </div>

      <div className="flex flex-col gap-2 w-full">
        <ModalButton
          text="Save"
          onClick={() => {
            fetcher.submit(formRef.current);
            onClose();
          }}
          className="bg-[#4465DB]"
        />
        <ModalButton text="Close" onClick={onClose} className="bg-[#737373]" />
      </div>

      <ModalButton
        variant="text-like"
        text="Delete Account"
        onClick={() => console.log("Delete Account")}
        className="text-danger self-start"
      />
    </ModalBody>
  );
}

export default AccountSettingsModal;
