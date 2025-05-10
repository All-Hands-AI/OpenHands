import React from "react";
import { ExtraProps } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { MermaidDiagram } from "./mermaid-diagram";

/**
 * Enhanced code component that handles Mermaid diagrams.
 * This extends the existing code component to detect and render Mermaid diagrams.
 */
export function mermaidCode({
  children,
  className,
  ...props
}: React.ClassAttributes<HTMLElement> &
  React.HTMLAttributes<HTMLElement> &
  ExtraProps) {
  const match = /language-(\w+)/.exec(className || ""); // get the language
  const codeContent = String(children).replace(/\n$/, "");
  
  // Check if this is a Mermaid code block
  if (match && match[1] === "mermaid") {
    return <MermaidDiagram code={codeContent} />;
  }

  // If not Mermaid, handle as regular code
  if (!match) {
    const isMultiline = codeContent.includes("\n");

    if (!isMultiline) {
      return (
        <code
          className={className}
          style={{
            backgroundColor: "#2a3038",
            padding: "0.2em 0.4em",
            borderRadius: "4px",
            color: "#e6edf3",
            border: "1px solid #30363d",
          }}
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <pre
        style={{
          backgroundColor: "#2a3038",
          padding: "1em",
          borderRadius: "4px",
          color: "#e6edf3",
          border: "1px solid #30363d",
          overflow: "auto",
        }}
      >
        <code className={className} {...props}>{codeContent}</code>
      </pre>
    );
  }

  return (
    <SyntaxHighlighter
      className="rounded-lg"
      style={vscDarkPlus}
      language={match?.[1]}
      PreTag="div"
      {...props}
    >
      {codeContent}
    </SyntaxHighlighter>
  );
}