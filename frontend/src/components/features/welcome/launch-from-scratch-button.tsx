import React from "react";

interface LaunchFromScratchButtonProps {
  onClick: () => void;
}

export function LaunchFromScratchButton({
  onClick,
}: LaunchFromScratchButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full bg-[#C9B775] text-black py-2 px-4 rounded-md font-medium hover:bg-[#D6C68A] transition-colors"
    >
      Launch From Scratch
    </button>
  );
}
