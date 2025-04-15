import DynamicText from "#/components/DynamicText"
import { CopyToClipboardButton } from "#/components/shared/buttons/copy-to-clipboard-button"
import Stepper from "#/components/Stepper"
import { cn } from "#/utils/utils"
import React from "react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { anchor } from "../markdown/anchor"
import { code } from "../markdown/code"
import { ol, ul } from "../markdown/list"
import videoSrc from "./agents-building-w-bg-animated.mp4"
import "./style.css"

interface ChatMessageProps {
  type: "user" | "assistant"
  message: string
  className?: string
  messageLength: number
}

const texts = [
  "Warming up the engines… Thank you for your patience!",
  "Hang tight, we’re working our magic…",
  "Pro tip: Great answers take time!",
  "Almost there – just booting up the AI brain…",
]

export function ChatMessage({
  type,
  message,
  children,
  className,
  messageLength,
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
    <>
      <article
        data-testid={`${type}-message`}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
        className={cn(
          "style-reset relative rounded-[20px]",
          "flex flex-col gap-2",
          type === "user" &&
            "max-w-[305px] self-end rounded-br-none border border-neutral-1000 bg-white px-4 py-2 dark:bg-gray-100",
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
            }}
            remarkPlugins={[remarkGfm]}
          >
            {message}
          </Markdown>
        </div>
        {children}
      </article>

      {type === "user" && messageLength === 1 && (
        <div>
          <Stepper />
          <div className="max-w-full rounded-[20px] bg-white p-4">
            <div className="flex items-center justify-center">
              <video
                preload="auto"
                muted={true}
                autoPlay
                playsInline
                loop
                controls={false}
                width={200}
                height={200}
                className="rounded-[20px]"
              >
                <source src={videoSrc} type="video/mp4" />
                <track kind="captions" />
              </video>
            </div>
            <DynamicText items={texts} />
          </div>
        </div>
      )}
    </>
  )
}
