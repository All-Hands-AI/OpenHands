import React from "react";
import { ExtraProps } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";

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
  const match = /language-(\w+)/.exec(className || ""); // get the language

  if (!match) {
    return <code className={className}>{children}</code>;
  }

  return (
    <SyntaxHighlighter
      className="rounded-lg"
      language={match?.[1]}
      PreTag="div"
    >
      {String(children).replace(/\n$/, "")}
    </SyntaxHighlighter>
  );
}
