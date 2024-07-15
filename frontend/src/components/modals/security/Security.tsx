import React from "react";
import SecurityInvariant from "./Invariant";
import BaseModal from "../base-modal/BaseModal";
import { getSettings } from "#/services/settings";

interface SecurityProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function Security({ isOpen, onOpenChange }: SecurityProps): JSX.Element {
  const { SECURITY_ANALYZER } = getSettings();

  return (
    <BaseModal
      isOpen={isOpen && !!SECURITY_ANALYZER}
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
