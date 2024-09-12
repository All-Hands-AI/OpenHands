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
      title="Are you sure you want to exit?"
      description="You will lose any unsaved information."
      buttons={[
        {
          text: "Exit Project",
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
