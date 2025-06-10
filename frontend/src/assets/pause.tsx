import React from "react";

function PauseIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      className="w-5 h-5 relative"
    >
      {/* Gray circle background */}
      <circle cx="12" cy="12" r="10" fill="#E5E7EB" />
      
      {/* Pause icon lines */}
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.75 5.25v13.5m-7.5-13.5v13.5"
        strokeWidth={1.5}
        stroke="currentColor"
      />
    </svg>
  );
}

export default PauseIcon;
