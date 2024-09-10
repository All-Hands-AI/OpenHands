import BaseModal from "./BaseModal";

interface ConfirmResetWorkspaceModalProps {
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmResetWorkspaceModal({
  onConfirm,
  onCancel,
}: ConfirmResetWorkspaceModalProps) {
  return (
    <BaseModal
      title="Are you sure you want to reset?"
      description="You will lose any unsaved information. This will clear your workspace and remove any prompts. Your current project will remain open."
      buttons={[
        {
          text: "Reset and Continue",
          onClick: onConfirm,
          className: "bg-danger",
        },
        {
          text: "Cancel",
          onClick: onCancel,
          className: "bg-[#737373]",
        },
      ]}
    />
  );
}

export default ConfirmResetWorkspaceModal;
