import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { mermaidCode } from "./mermaid-code";
import { ul, ol } from "../markdown/list";
import { anchor } from "../markdown/anchor";

/**
 * Example of how to integrate the Mermaid component into the ChatMessage component.
 * This is a modified version of the existing ChatMessage component.
 */
export function ChatMessageWithMermaid({
  type,
  message,
  children,
}: React.PropsWithChildren<{
  type: "user" | "assistant";
  message: string;
}>) {
  const [isHovering, setIsHovering] = React.useState(false);
  const [isCopy, setIsCopy] = React.useState(false);

  const handleCopyToClipboard = async () => {
    await navigator.clipboard.writeText(message);
    setIsCopy(true);
    setTimeout(() => setIsCopy(false), 2000);
  };

  return (
    <article
      data-testid={`${type}-message`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className={`rounded-xl relative flex flex-col gap-2 ${
        type === "user" ? "max-w-[305px] p-4 bg-tertiary self-end" : "mt-6 max-w-full bg-transparent"
      }`}
    >
      <div className="text-sm break-words">
        <Markdown
          components={{
            code: mermaidCode, // Use the enhanced code component that handles Mermaid
            ul,
            ol,
            a: anchor,
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

/**
 * Example usage:
 * 
 * <ChatMessageWithMermaid
 *   type="assistant"
 *   message={`Here's a flowchart:
 * 
 * \`\`\`mermaid
 * graph TD
 *     A[Start] --> B{Is it working?}
 *     B -->|Yes| C[Great!]
 *     B -->|No| D[Debug]
 *     D --> B
 * \`\`\`
 * 
 * This diagram shows a simple debugging process.`}
 * />
 */