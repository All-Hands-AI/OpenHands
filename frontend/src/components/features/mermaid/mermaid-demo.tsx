import React, { useState } from "react";
import { MarkdownWithMermaid } from "./markdown-integration";

/**
 * Demo component to showcase Mermaid diagram rendering.
 * This component provides a textarea for editing Mermaid code and displays the rendered diagram.
 */
export function MermaidDemo() {
  const [diagramCode, setDiagramCode] = useState(`# Mermaid Diagram Demo

Here's a flowchart diagram:

\`\`\`mermaid
graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
\`\`\`

Here's a sequence diagram:

\`\`\`mermaid
sequenceDiagram
    participant User
    participant System
    User->>System: Request data
    System->>Database: Query data
    Database-->>System: Return results
    System-->>User: Display results
\`\`\`

Here's a class diagram:

\`\`\`mermaid
classDiagram
    class Animal {
        +name: string
        +age: int
        +makeSound(): void
    }
    class Dog {
        +breed: string
        +bark(): void
    }
    class Cat {
        +color: string
        +meow(): void
    }
    Animal <|-- Dog
    Animal <|-- Cat
\`\`\`
`);

  return (
    <div className="mermaid-demo p-4">
      <h1 className="text-2xl font-bold mb-4">Mermaid Diagram Demo</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="editor-pane">
          <h2 className="text-lg font-semibold mb-2">Edit Markdown with Mermaid</h2>
          <textarea
            className="w-full h-[500px] p-2 border border-gray-300 rounded font-mono text-sm"
            value={diagramCode}
            onChange={(e) => setDiagramCode(e.target.value)}
          />
        </div>
        
        <div className="preview-pane">
          <h2 className="text-lg font-semibold mb-2">Preview</h2>
          <div className="border border-gray-300 rounded p-4 h-[500px] overflow-auto">
            <MarkdownWithMermaid content={diagramCode} />
          </div>
        </div>
      </div>
    </div>
  );
}