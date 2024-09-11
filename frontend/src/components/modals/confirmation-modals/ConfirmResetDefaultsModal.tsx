import BaseModal from "./BaseModal";

interface ConfirmResetDefaultsModalProps {
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmResetDefaultsModal({
  onConfirm,
  onCancel,
}: ConfirmResetDefaultsModalProps) {
  return (
    <BaseModal
      title="Are you sure?"
      description="All saved information in your AI settings will be deleted including any API keys."
      buttons={[
        {
          text: "Reset Defaults",
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

export default ConfirmResetDefaultsModal;
