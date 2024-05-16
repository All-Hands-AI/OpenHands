import React from "react";
import Markdown from "react-markdown";
import { twMerge } from "tailwind-merge";
import { code } from "../markdown/code";

interface MessageProps {
  message: Message;
  className?: string; // Add a className prop for custom styling
}

function ChatMessage({ message, className: customClassName }: MessageProps) {
  // const text = useTyping(message.content);

  const className = twMerge(
    "p-3 text-white max-w-[90%] overflow-y-auto rounded-lg",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
    customClassName, // Apply custom className if provided
  );

  return (
    <div data-testid="message" className={className}>
      <Markdown components={{ code }}>{message.content}</Markdown>
    </div>
  );
}

export default ChatMessage;
