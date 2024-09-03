import React from "react";
import BaseModal from "./BaseModal";

function ConfirmExitProjectModal() {
  return (
    <BaseModal
      title="Are you sure you want to exit?"
      description="You will lose any unsaved information."
      buttons={[
        {
          text: "Exit Project",
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

export default ConfirmExitProjectModal;
