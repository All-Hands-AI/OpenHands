import React from "react";

function PauseIcon() {
  return (
    <div className="relative flex items-center justify-center w-6 h-6">
      {/* Gray circle background */}
      <div className="absolute w-6 h-6 bg-gray-200 rounded-full" />
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="w-5 h-5 relative z-10"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15.75 5.25v13.5m-7.5-13.5v13.5"
        />
      </svg>
    </div>
  );
}

export default PauseIcon;
