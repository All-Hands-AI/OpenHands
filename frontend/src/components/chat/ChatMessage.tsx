import React from "react";
import Markdown from "react-markdown";
import { ClipboardCopyIcon } from '@heroicons/react/outline';
import { twMerge } from "tailwind-merge";
import { code } from "../markdown/code";
import { useTyping } from "#/hooks/useTyping";

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  const text = useTyping(message.content);

  const className = twMerge(
    "p-3 text-white max-w-[85%] md:max-w-[90%] overflow-y-auto rounded-lg",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
  );

  function handleCopy() {
    navigator.clipboard.writeText(message.content);
  }

  return (
    <div data-testid="message" className={className}>
      <Markdown components={{ code }}>{text}</Markdown>
      <button onClick={handleCopy} className="ml-2">
        <ClipboardCopyIcon className="h-5 w-5 text-white" />
      </button>
    </div>
  );
}

export default ChatMessage;
