import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { cn } from "#/utils/utils";
import { ul, ol } from "../markdown/list";
import { anchor } from "../markdown/anchor";
import { MessageActions } from "./message-actions";
import { useHover } from "#/hooks/use-hover";
import { OpenHandsSourceType } from "#/types/core/base";
import { paragraph } from "../markdown/paragraph";

interface ChatMessageProps {
  type: OpenHandsSourceType;
  message: string;
  messageId?: number;
  feedback?: "positive" | "negative" | null;
}

export function ChatMessage({
  type,
  message,
  messageId,
  feedback,
  children,
}: React.PropsWithChildren<ChatMessageProps>) {
  const [isHovering, hoverProps] = useHover();
  const [isCopy, setIsCopy] = React.useState(false);

  const handleCopyToClipboard = async () => {
    await navigator.clipboard.writeText(message);
    setIsCopy(true);
  };

  React.useEffect(() => {
    let timeout: NodeJS.Timeout;

    if (isCopy) {
      timeout = setTimeout(() => {
        setIsCopy(false);
      }, 2000);
    }

    return () => {
      clearTimeout(timeout);
    };
  }, [isCopy]);

  return (
    <article
      data-testid={`${type}-message`}
      onMouseEnter={hoverProps.onMouseEnter}
      onMouseLeave={hoverProps.onMouseLeave}
      className={cn(
        "rounded-xl relative",
        "flex flex-col gap-2",
        type === "user" && " max-w-[305px] p-4 bg-tertiary self-end",
        type === "agent" && "mt-6 max-w-full bg-transparent",
      )}
    >
      {/* Action buttons */}
      {type === "assistant" && (
        <MessageActions
          messageId={messageId}
          feedback={feedback}
          isHovering={isHovering}
          isCopy={isCopy}
          onCopy={handleCopyToClipboard}
        />
      )}

      <div className="text-sm break-words">
        <Markdown
          components={{
            code,
            ul,
            ol,
            a: anchor,
            p: paragraph,
          }}
          remarkPlugins={[remarkGfm]}
        >
          {message}
        </Markdown>
      </div>

      {children}
    </article>
  );
}
