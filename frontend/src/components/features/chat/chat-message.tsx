import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { cn } from "#/utils/utils";
import { ul, ol } from "../markdown/list";
import { CopyToClipboardButton } from "#/components/shared/buttons/copy-to-clipboard-button";
import { anchor } from "../markdown/anchor";

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
        type === "assistant" && "mt-6 max-w-full bg-tranparent",
      )}
    >
      <CopyToClipboardButton
        isHidden={!isHovering}
        isDisabled={isCopy}
        onClick={handleCopyToClipboard}
        mode={isCopy ? "copied" : "copy"}
      />
      <Markdown
        className="text-sm overflow-auto"
        components={{
          code,
          ul,
          ol,
          a: anchor,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {message}
      </Markdown>
      {children}
    </article>
  );
}
