import React, { useState } from "react";
import Markdown from "react-markdown";
import { FaClipboard } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { useTranslation } from "react-i18next";
import { code } from "../markdown/code";
import toast from "#/utils/toast";
import { I18nKey } from "#/i18n/declaration";

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  const [isHovering, setIsHovering] = useState(false);

  const className = twMerge(
    "p-3 max-w-[90%] overflow-y-auto rounded-lg relative border-2 shadow-md",
    message.sender === "user"
      ? "bg-user-message-bg text-user-message-text self-end border-blue-500 dark:border-blue-400"
      : "bg-assistant-message-bg text-assistant-message-text border-green-500 dark:border-green-400",
  );

  const { t } = useTranslation();
  const copyToClipboard = () => {
    navigator.clipboard
      .writeText(message.content)
      .then(() => {
        toast.info(t(I18nKey.CHAT_INTERFACE$CHAT_MESSAGE_COPIED));
      })
      .catch(() => {
        toast.error(
          "copy-error",
          t(I18nKey.CHAT_INTERFACE$CHAT_MESSAGE_COPY_FAILED),
        );
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
          className="absolute top-1 right-1 p-1 bg-neutral-600 dark:bg-neutral-700 rounded hover:bg-neutral-500 dark:hover:bg-neutral-600 transition-opacity opacity-75 hover:opacity-100"
          aria-label={t(I18nKey.CHAT_INTERFACE$TOOLTIP_COPY_MESSAGE)}
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
