import { ModalBackdrop } from "../modal-backdrop";
import { AccountSettingsForm } from "./account-settings-form";

interface AccountSettingsModalProps {
  onClose: () => void;
}

export function AccountSettingsModal({ onClose }: AccountSettingsModalProps) {
  return (
    <ModalBackdrop onClose={onClose}>
      <AccountSettingsForm onClose={onClose} />
    </ModalBackdrop>
  );
}
