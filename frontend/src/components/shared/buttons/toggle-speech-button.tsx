import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "#/store";
import { toggleSpeech } from "#/state/speech-slice";
import { cn } from "#/utils/utils";

export function ToggleSpeechButton() {
  const dispatch = useDispatch();
  const enabled = useSelector((state: RootState) => state.speech.enabled);

  return (
    <button
      type="button"
      onClick={() => dispatch(toggleSpeech())}
      className={cn(
        "flex items-center justify-center",
        "w-8 h-8 rounded-lg",
        "hover:bg-neutral-700 transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-neutral-500",
      )}
      title={enabled ? "Disable speech" : "Enable speech"}
    >
      {/* Speaker icon - filled when enabled, outline when disabled */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill={enabled ? "currentColor" : "none"}
        stroke="currentColor"
        className="w-5 h-5"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
        />
      </svg>
    </button>
  );
}
