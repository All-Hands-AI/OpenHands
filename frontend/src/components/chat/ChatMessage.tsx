import React, { useState } from "react";
import Markdown from "react-markdown";
import { FaClipboard, FaClipboardCheck } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { useTranslation } from "react-i18next";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import toast from "#/utils/toast";
import { I18nKey } from "#/i18n/declaration";
import ConfirmationButtons from "./ConfirmationButtons";
import { formatTimestamp } from "#/utils/utils";

interface MessageProps {
  message: Message;
  isLastMessage?: boolean;
  awaitingUserConfirmation?: boolean;
}

function ChatMessage({
  message,
  isLastMessage,
  awaitingUserConfirmation,
}: MessageProps) {
  const { t } = useTranslation();

  const [isCopy, setIsCopy] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  React.useEffect(() => {
    let timeout: NodeJS.Timeout;

    if (isCopy) {
      timeout = setTimeout(() => {
        setIsCopy(false);
      }, 1500);
    }

    return () => {
      clearTimeout(timeout);
    };
  }, [isCopy]);

  const className = twMerge(
    "markdown-body",
    "p-3 text-white max-w-[90%] overflow-y-auto rounded-lg relative",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
  );

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setIsCopy(true);

      toast.info(t(I18nKey.CHAT_INTERFACE$CHAT_MESSAGE_COPIED));
    } catch {
      toast.error(
        "copy-error",
        t(I18nKey.CHAT_INTERFACE$CHAT_MESSAGE_COPY_FAILED),
      );
    }
  };

  const copyButtonTitle = message.timestamp
    ? `${t(I18nKey.CHAT_INTERFACE$TOOLTIP_COPY_MESSAGE)} - ${formatTimestamp(message.timestamp)}`
    : t(I18nKey.CHAT_INTERFACE$TOOLTIP_COPY_MESSAGE);

  return (
    <article
      data-testid="article"
      className={className}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      aria-label={t(I18nKey.CHAT_INTERFACE$MESSAGE_ARIA_LABEL, {
        sender: message.sender
          ? message.sender.charAt(0).toUpperCase() +
            message.sender.slice(1).toLowerCase()
          : t(I18nKey.CHAT_INTERFACE$UNKNOWN_SENDER),
      })}
    >
      {isHovering && (
        <button
          data-testid="copy-button"
          onClick={copyToClipboard}
          className="absolute top-1 right-1 p-1 bg-neutral-600 rounded hover:bg-neutral-700"
          aria-label={copyButtonTitle}
          title={copyButtonTitle}
          type="button"
        >
          {isCopy ? <FaClipboardCheck /> : <FaClipboard />}
        </button>
      )}
      <Markdown components={{ code }} remarkPlugins={[remarkGfm]}>
        {message.content}
      </Markdown>
      {(message.imageUrls?.length ?? 0) > 0 && (
        <div className="flex space-x-2 mt-2">
          {message.imageUrls?.map((url, index) => (
            <img
              key={index}
              src={url}
              alt={`upload preview ${index}`}
              className="w-24 h-24 object-contain rounded bg-white"
            />
          ))}
        </div>
      )}
      {isLastMessage &&
        message.sender === "assistant" &&
        awaitingUserConfirmation && <ConfirmationButtons />}
    </article>
  );
}

export default ChatMessage;
