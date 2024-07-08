import React from "react";

function TypingIndicator(): React.ReactElement {
  return (
    <div className="flex items-center space-x-1.5 bg-neutral-700 px-3 py-1.5 rounded-full">
      <span
        className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-[bounce_0.5s_infinite] translate-y-[-2px]"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-[bounce_0.5s_infinite] translate-y-[-2px]"
        style={{ animationDelay: "75ms" }}
      />
      <span
        className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-[bounce_0.5s_infinite] translate-y-[-2px]"
        style={{ animationDelay: "150ms" }}
      />
    </div>
  );
}

export default TypingIndicator;
