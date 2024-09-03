import React from "react";
import BaseModal from "./BaseModal";

function ConfirmCreateAndReplaceProjectModal() {
  return (
    <BaseModal
      title="Creating a New Project will replace your active project"
      description="No information will be saved. If you want to save your project cancel and either download the project or save it to GitHub."
      buttons={[
        {
          text: "Continue",
          onClick: () => console.log("Create New Project"),
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

export default ConfirmCreateAndReplaceProjectModal;
