import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import CheckmarkIcon from "#/icons/checkmark.svg?react";
import CopyIcon from "#/icons/copy.svg?react";
import { code } from "./markdown/code";
import { cn } from "#/utils/utils";
import { ul, ol } from "./markdown/list";

interface ChatMessageProps {
  type: "user" | "assistant";
  message: string;
}

export function ChatMessage({
  type,
  message,
  children,
}: React.PropsWithChildren<ChatMessageProps>) {
  const [isHovering, setIsHovering] = React.useState(false);
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
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className={cn(
        "rounded-xl relative",
        "flex flex-col gap-2",
        type === "user" && " max-w-[305px] p-4 bg-neutral-700 self-end",
        type === "assistant" && "pb-4 max-w-full bg-tranparent",
      )}
    >
      <button
        hidden={!isHovering}
        disabled={isCopy}
        data-testid="copy-to-clipboard"
        type="button"
        onClick={handleCopyToClipboard}
        className={cn(
          "bg-neutral-700 border border-neutral-600 rounded p-1",
          "absolute top-1 right-1",
        )}
      >
        {!isCopy ? (
          <CopyIcon width={15} height={15} />
        ) : (
          <CheckmarkIcon width={15} height={15} />
        )}
      </button>
      <Markdown
        className="text-sm overflow-auto"
        components={{
          code,
          ul,
          ol,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {message}
      </Markdown>
      {children}
    </article>
  );
}
