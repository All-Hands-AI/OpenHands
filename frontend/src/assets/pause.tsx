import React from "react";

function PauseIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className="w-5 h-5"
    >
      {/* Gray circle background */}
      <circle cx="12" cy="12" r="10" fill="#4B5563" opacity="0.85" />
      
      {/* Pause icon lines */}
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.75 5.25v13.5m-7.5-13.5v13.5"
        stroke="white"
        strokeWidth="2"
      />
    </svg>
  );
}

export default PauseIcon;
