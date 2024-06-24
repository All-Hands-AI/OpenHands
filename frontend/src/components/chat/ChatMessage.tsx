import React from "react";
import Markdown from "react-markdown";
import { twMerge } from "tailwind-merge";
import { code } from "../markdown/code";
import { FaClipboard } from "react-icons/fa";
import toast from "#/utils/toast"; // Assuming you have a toast utility for notifications

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  const className = twMerge(
    "markdown-body",
    "p-3 text-white max-w-[90%] overflow-y-auto rounded-lg",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
  );

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content).then(() => {
      toast.info("Message copied to clipboard!");
    }).catch((error) => {
      toast.error(`Failed to copy message: ${error}`);
    });
  };

  return (
    <div data-testid="message" className={className}>
      <div className="flex justify-between items-center">
        <Markdown components={{ code }}>{message.content}</Markdown>
        <button
          onClick={copyToClipboard}
          className="ml-2 p-1 bg-neutral-600 rounded hover:bg-neutral-500"
          aria-label="Copy message"
        >
          <FaClipboard />
        </button>
      </div>
    </div>
  );
}

export default ChatMessage;