import React from "react";
import SecurityInvariant from "./Invariant";
import BaseModal from "../base-modal/BaseModal";

interface SecurityProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function Security({ isOpen, onOpenChange }: SecurityProps): JSX.Element {
  return (
    <BaseModal
      isOpen={isOpen}
      contentClassName="max-w-[80%] min-h-[80%]"
      bodyClassName="px-0 py-0"
      onOpenChange={onOpenChange}
      title=""
    >
      <SecurityInvariant />
    </BaseModal>
  );
}

export default Security;
