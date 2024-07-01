import React, { useState } from "react";
import Markdown from "react-markdown";
import { FaClipboard, FaClipboardCheck } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { useTranslation } from "react-i18next";
import { code } from "../markdown/code";
import toast from "#/utils/toast";
import { I18nKey } from "#/i18n/declaration";

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  const [isCopy, setIsCopy] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const className = twMerge(
    "markdown-body",
    "p-3 text-white max-w-[90%] overflow-y-auto rounded-lg relative",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
  );

  const { t } = useTranslation();
  const copyToClipboard = () => {
    navigator.clipboard
      .writeText(message.content)
      .then(() => {
        setIsCopy(true);
        setTimeout(() => {
          setIsCopy(false);
        }, 1500);
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
          className="absolute top-1 right-1 p-1 bg-neutral-600 rounded hover:bg-neutral-700"
          aria-label={t(I18nKey.CHAT_INTERFACE$TOOLTIP_COPY_MESSAGE)}
          type="button"
        >
          {isCopy ? <FaClipboardCheck /> : <FaClipboard />}
        </button>
      )}
      <Markdown components={{ code }}>{message.content}</Markdown>
    </div>
  );
}

export default ChatMessage;
