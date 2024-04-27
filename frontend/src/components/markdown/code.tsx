import React from "react";
import { ExtraProps } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

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
    <SyntaxHighlighter style={vscDarkPlus} language={match?.[1]} PreTag="div">
      {String(children).replace(/\n$/, "")}
    </SyntaxHighlighter>
  );
}
