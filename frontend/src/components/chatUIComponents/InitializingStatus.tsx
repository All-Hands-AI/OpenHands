import React from "react";
import assistantAvatar from "../../assets/assistant-avatar.png";

function InitializingStatus(): JSX.Element {
  return (
    <div className="flex items-center m-auto h-full">
      <img
        src={assistantAvatar}
        alt="assistant avatar"
        className="w-[40px] h-[40px] mx-2.5"
      />
      <div>Initializing agent (may take up to 10 seconds)...</div>
    </div>
  );
}

export default InitializingStatus;
