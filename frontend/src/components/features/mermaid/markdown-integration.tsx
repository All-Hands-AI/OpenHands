import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { mermaidCode } from "./mermaid-code";

/**
 * Example of how to integrate the Mermaid component into the existing markdown renderer.
 * This shows how to extend the components prop of react-markdown to include Mermaid support.
 */
export function MarkdownWithMermaid({ content }: { content: string }) {
  return (
    <Markdown
      components={{
        // Add the mermaidCode component to handle code blocks
        code: mermaidCode,
        // Include any other custom components used in the existing markdown renderer
      }}
      remarkPlugins={[remarkGfm]}
    >
      {content}
    </Markdown>
  );
}

/**
 * Example usage:
 * 
 * ```tsx
 * <MarkdownWithMermaid 
 *   content={`
 * # Diagram Example
 * 
 * Here's a flowchart:
 * 
 * \`\`\`mermaid
 * graph TD
 *     A[Start] --> B{Is it working?}
 *     B -->|Yes| C[Great!]
 *     B -->|No| D[Debug]
 *     D --> B
 * \`\`\`
 * 
 * This diagram shows a simple debugging process.
 * `} 
 * />
 * ```
 */