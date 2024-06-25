// frontend/src/components/chat/TypingIndicator.tsx
import React from "react";

const TypingIndicator = () => (
  <div className="flex items-center space-x-2">
    <span className="w-2.5 h-2.5 bg-gray-400 rounded-full animate-bounce"></span>
    <span className="w-2.5 h-2.5 bg-gray-400 rounded-full animate-bounce delay-200"></span>
    <span className="w-2.5 h-2.5 bg-gray-400 rounded-full animate-bounce delay-400"></span>
  </div>
);

export default TypingIndicator;