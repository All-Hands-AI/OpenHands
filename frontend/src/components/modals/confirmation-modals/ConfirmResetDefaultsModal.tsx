import React from "react";
import BaseModal from "./BaseModal";

function ConfirmResetDefaultsModal() {
  return (
    <BaseModal
      title="Are you sure?"
      description="All saved information in your AI settings will be deleted including any API keys."
      buttons={[
        {
          text: "Reset Defaults",
          onClick: () => console.log("Delete"),
          className: "bg-danger",
        },
        {
          text: "Cancel",
          onClick: () => console.log("Cancel"),
          className: "bg-[#737373]",
        },
      ]}
    />
  );
}

export default ConfirmResetDefaultsModal;
