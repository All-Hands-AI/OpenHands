import React from "react";
import ModalButton from "../buttons/ModalButton";
import LoadingSpinnerOuter from "#/assets/loading-outer.svg?react";
import ModalBody from "./ModalBody";

function LoadingSpinner() {
  return (
    <div className="relative w-[60px] h-[60px]">
      <div className="w-[60px] h-[60px] rounded-full border-4 border-[#525252] absolute" />
      <LoadingSpinnerOuter className="absolute w-[60px] h-[60px] animate-spin" />
    </div>
  );
}

function LoadingProjectModal() {
  return (
    <ModalBody>
      <span className="text-xl leading-6 -tracking-[0.01em] font-semibold">
        Your project is loading...
      </span>
      <LoadingSpinner />
      <ModalButton
        onClick={() => console.log("cancel")}
        text="Cancel"
        className="bg-[#737373] w-full"
      />
    </ModalBody>
  );
}

export default LoadingProjectModal;
