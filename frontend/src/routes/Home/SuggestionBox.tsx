import React from "react";

interface SuggestionBoxProps {
  title: string;
  description: string;
}

export function SuggestionBox({ title, description }: SuggestionBoxProps) {
  return (
    <button
      type="button"
      className="w-[304px] h-[100px] border border-[#525252] rounded-xl flex flex-col items-center justify-center"
    >
      <span className="text-[16px] leading-6 -tracking-[0.01em] font-[600]">
        {title}
      </span>
      <span className="text-sm">{description}</span>
    </button>
  );
}
