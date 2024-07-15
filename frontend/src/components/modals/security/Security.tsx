import React from "react";
import SecurityInvariant from "./Invariant";
import BaseModal from "../base-modal/BaseModal";
import { getSettings } from "#/services/settings";
import toast from "#/utils/toast";

interface SecurityProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function Security({ isOpen, onOpenChange }: SecurityProps): JSX.Element {
  const { SECURITY_ANALYZER } = getSettings();

  if (!SECURITY_ANALYZER) {
    toast.error("security", "Enable security analyzer from settings.");
    return <div />;
  }

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
