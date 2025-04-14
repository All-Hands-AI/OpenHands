import { CopyToClipboardButton } from "#/components/shared/buttons/copy-to-clipboard-button"
import { cn } from "#/utils/utils"
import React from "react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { anchor } from "../markdown/anchor"
import { code } from "../markdown/code"
import { ol, ul } from "../markdown/list"
import "./style.css"

interface ChatMessageProps {
  type: "user" | "assistant"
  message: string
  className?: string
}

export function ChatMessage({
  type,
  message,
  children,
  className,
}: React.PropsWithChildren<ChatMessageProps>) {
  const [isHovering, setIsHovering] = React.useState(false)
  const [isCopy, setIsCopy] = React.useState(false)

  const handleCopyToClipboard = async () => {
    await navigator.clipboard.writeText(message)
    setIsCopy(true)
  }

  React.useEffect(() => {
    let timeout: NodeJS.Timeout

    if (isCopy) {
      timeout = setTimeout(() => {
        setIsCopy(false)
      }, 2000)
    }

    return () => {
      clearTimeout(timeout)
    }
  }, [isCopy])

  return (
    <article
      data-testid={`${type}-message`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className={cn(
        "style-reset relative rounded-[20px]",
        "flex flex-col gap-2",
        type === "user" &&
          "max-w-[75%] self-end rounded-br-none border border-neutral-1000 bg-white px-4 py-2 dark:bg-gray-100",
        type === "assistant" && "mt-2 max-w-full bg-transparent",
        className,
      )}
    >
      <CopyToClipboardButton
        isHidden={!isHovering}
        isDisabled={isCopy}
        onClick={handleCopyToClipboard}
        mode={isCopy ? "copied" : "copy"}
      />
      <div className="overflow-auto break-words text-sm text-neutral-100 dark:text-white">
        <Markdown
          components={{
            code,
            ul,
            ol,
            a: anchor,
            pre: ({ children }) => (
              <pre className="[&_pre]:my-0 [&_pre]:whitespace-pre-wrap [&_pre]:border-none [&_pre]:bg-white [&_pre]:p-0 [&_pre]:text-neutral-100 [&_pre_code]:!font-inter">
                {children}
              </pre>
            ),
          }}
          remarkPlugins={[remarkGfm]}
        >
          {message}
        </Markdown>
      </div>
      {children}
    </article>
  )
}
