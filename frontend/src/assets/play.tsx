import React from "react";

function PlayIcon() {
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
          d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"
        />
      </svg>
    </div>
  );
}

export default PlayIcon;
