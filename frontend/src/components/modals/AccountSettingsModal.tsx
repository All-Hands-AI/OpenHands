import React from "react";
import { BaseModalTitle } from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import FormFieldset from "../form/FormFieldset";

function AccountSettingsModal() {
  return (
    <ModalBody>
      <div className="w-full flex flex-col gap-2">
        <BaseModalTitle title="Account Settings" />
        <FormFieldset
          id="language"
          label="Language"
          defaultSelectedKey="en"
          isClearable={false}
          items={[
            { key: "en", value: "English" },
            { key: "es", value: "Spanish" },
            { key: "fr", value: "French" },
          ]}
        />
      </div>

      <div className="flex flex-col gap-2 w-full">
        <ModalButton
          text="Save"
          onClick={() => console.log("Save")}
          className="bg-[#4465DB]"
        />
        <ModalButton
          text="Close"
          onClick={() => console.log("Close")}
          className="bg-[#737373]"
        />
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
