import React, { useState } from "react";
import Markdown from "react-markdown";
import { FaClipboard } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { code } from "../markdown/code";
import toast from "#/utils/toast";

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  const [isHovering, setIsHovering] = useState(false);

  const className = twMerge(
    "markdown-body",
    "p-3 text-white max-w-[90%] overflow-y-auto rounded-lg relative",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
  );

  const copyToClipboard = () => {
    navigator.clipboard
      .writeText(message.content)
      .then(() => {
        toast.info("Message copied to clipboard!");
      })
      .catch((error) => {
        toast.error("copy-error", `Failed to copy message: ${error}`);
      });
  };

  return (
    <div
      data-testid="message"
      className={className}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {isHovering && (
        <button
          onClick={copyToClipboard}
          className="absolute top-1 right-1 p-1 bg-neutral-600 rounded hover:bg-neutral-500 transition-opacity opacity-75 hover:opacity-100"
          aria-label="Copy message"
          type="button"
        >
          <FaClipboard />
        </button>
      )}
      <Markdown components={{ code }}>{message.content}</Markdown>
    </div>
  );
}

export default ChatMessage;
