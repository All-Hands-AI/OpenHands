import CopyIcon from "public/icons/copy.svg?react";
import CheckmarkIcon from "public/icons/checkmark.svg?react";
import React from "react";
import { cn } from "#/utils/utils";

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
        "p-4 rounded-xl max-w-[305px] relative",
        "flex flex-col gap-2",
        type === "user" && "bg-neutral-700 self-end",
        type === "assistant" && "bg-tranparent",
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
      <p className="text-sm overflow-auto">{message}</p>
      {children}
    </article>
  );
}
