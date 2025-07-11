import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { cn } from "#/utils/utils";
import { ul, ol } from "../markdown/list";
import { CopyToClipboardButton } from "#/components/shared/buttons/copy-to-clipboard-button";
import { anchor } from "../markdown/anchor";
import { OpenHandsSourceType } from "#/types/core/base";
import { paragraph } from "../markdown/paragraph";

interface ChatMessageProps {
  type: OpenHandsSourceType;
  message: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
  }>;
}

export function ChatMessage({
  type,
  message,
  children,
  actions,
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
        "rounded-xl relative w-fit",
        "flex flex-col gap-2",
        type === "user" && " max-w-[305px] p-4 bg-tertiary self-end",
        type === "agent" && "mt-6 max-w-full bg-transparent",
      )}
    >
      <div
        className={cn(
          "absolute -top-2.5 -right-2.5",
          !isHovering ? "hidden" : "flex",
          "items-center gap-1",
        )}
      >
        {actions?.map((action, index) => (
          <button
            key={index}
            type="button"
            onClick={action.onClick}
            className="button-base p-1 cursor-pointer"
            aria-label={`Action ${index + 1}`}
          >
            {action.icon}
          </button>
        ))}

        <CopyToClipboardButton
          isHidden={!isHovering}
          isDisabled={isCopy}
          onClick={handleCopyToClipboard}
          mode={isCopy ? "copied" : "copy"}
        />
      </div>

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
