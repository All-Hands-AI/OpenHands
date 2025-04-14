import { cn } from "#/utils/utils"
import React from "react"
import { ExtraProps } from "react-markdown"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import oneLight from "react-syntax-highlighter/dist/cjs/styles/prism/one-light"
// import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

// See https://github.com/remarkjs/react-markdown?tab=readme-ov-file#use-custom-components-syntax-highlight

/**
 * Component to render code blocks in markdown.
 */
export function code({
  children,
  className,
}: React.ClassAttributes<HTMLElement> &
  React.HTMLAttributes<HTMLElement> &
  ExtraProps) {
  const match = /language-(\w+)/.exec(className || "") // get the language

  if (!match) {
    const isMultiline = String(children).includes("\n")

    if (!isMultiline) {
      return (
        <code
          className={cn(
            "border border-neutral-1000 bg-white font-inter text-neutral-100 dark:border-[#30363d] dark:bg-[#2a3038] dark:text-white",
            className,
          )}
          style={{
            padding: "0.2em 0.4em",
            borderRadius: "4px",
          }}
        >
          {children}
        </code>
      )
    }

    return (
      <pre className="overflow-auto border border-neutral-1000 bg-white p-4 font-inter text-neutral-100 dark:border-[#30363d] dark:bg-[#2a3038] dark:text-white">
        <code className={className}>{String(children).replace(/\n$/, "")}</code>
      </pre>
    )
  }

  return (
    <SyntaxHighlighter
      className="rounded-lg"
      style={oneLight}
      language={match?.[1]}
      PreTag="div"
    >
      {String(children).replace(/\n$/, "")}
    </SyntaxHighlighter>
  )
}
