import React from "react";
import BaseModal from "./BaseModal";

function ConfirmDeleteAccountModal() {
  return (
    <BaseModal
      title="Are you sure?"
      description="Deleting your account will remove any information saved by All Hands."
      buttons={[
        {
          text: "Delete Account",
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

export default ConfirmDeleteAccountModal;
