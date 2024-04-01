import React from "react";
import assistantAvatar from "../assets/assistant-avatar.png";

export default function Loader() {
  return (
    <div className="flex-col gap-4 w-full flex items-center justify-center">
      <div className="w-20 h-20 border-8 text-blue-400 text-4xl animate-spin border-gray-300 flex items-center justify-center border-t-blue-400 rounded-full">
        <img
          src={assistantAvatar}
          alt="assistant avatar"
          height="20px"
          width="20px"
          className="animate-ping"
        />
      </div>
    </div>
  );
}
