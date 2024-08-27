import React from "react";
import PlayIcon from "#/assets/play.svg?react";

export function PlayPauseButton() {
  return (
    <button
      type="button"
      aria-label="Play"
      className="w-[52px] h-[52px] rounded-full bg-[#262626] flex items-center justify-center"
    >
      <PlayIcon width={24} height={24} />
    </button>
  );
}
