import React from "react";
import BaseModal from "./BaseModal";

function ConfirmResetWorkspaceModal() {
  return (
    <BaseModal
      title="Are you sure you want to reset?"
      description="You will lose any unsaved information. This will clear your workspace and remove any prompts. Your current project will remain open."
      buttons={[
        {
          text: "Reset Workspace",
          onClick: () => console.log("Reset"),
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

export default ConfirmResetWorkspaceModal;
