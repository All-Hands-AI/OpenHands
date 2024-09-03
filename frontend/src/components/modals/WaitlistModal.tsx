import React from "react";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import ModalButton from "../buttons/ModalButton";
import Clipboard from "#/assets/clipboard.svg?react";
import ModalBody from "./ModalBody";

function WaitlistModal() {
  return (
    <ModalBody>
      <Clipboard className="self-center w-[54px] h-[75px]" />
      <div className="flex flex-col gap-2">
        <BaseModalTitle title="You've been added to our waitlist!" />
        <BaseModalDescription description="We're a bit overloaded at the moment-we've added you to the waitlist. We'll send you an email at foo@example.com when your account is ready!" />
      </div>
      <ModalButton
        text="Return to Mainpage"
        onClick={() => console.log("Return to Mainpage")}
        className="bg-[#737373] w-full"
      />
    </ModalBody>
  );
}

export default WaitlistModal;
