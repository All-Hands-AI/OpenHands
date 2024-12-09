import React from "react";
import { ExtraProps } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import ansiHTML from 'ansi-html-community';

// Initialize ansi-html with VSCode Dark Plus theme colors
ansiHTML.setColors({
  reset: ['fff', '1e1e1e'], // text color, background color
  black: '1e1e1e',
  red: 'f14c4c',
  green: '23d18b',
  yellow: 'f5f543',
  blue: '3b8eea',
  magenta: 'd670d6',
  cyan: '29b8db',
  lightgrey: 'abb2bf',
  darkgrey: '5c6370'
});

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
  const content = String(children).replace(/\n$/, "");

  // If the content contains ANSI escape codes, render with ansi-html
  if (content.includes('\u001b[')) {
    return (
      <pre 
        className="rounded-lg p-4 bg-[#1e1e1e]"
        dangerouslySetInnerHTML={{ __html: ansiHTML(content) }}
      />
    );
  }

  // Otherwise use syntax highlighting
  if (!match) {
    return <code className={className}>{children}</code>;
  }

  return (
    <SyntaxHighlighter
      className="rounded-lg"
      style={vscDarkPlus}
      language={match?.[1]}
      PreTag="div"
    >
      {content}
    </SyntaxHighlighter>
  );
}
