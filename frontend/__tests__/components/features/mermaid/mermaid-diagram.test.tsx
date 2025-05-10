import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MermaidDiagram } from "../../../../src/components/features/mermaid/mermaid-diagram";

// Mock the clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

describe("MermaidDiagram", () => {
  const sampleCode = `graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B`;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the diagram container", () => {
    render(<MermaidDiagram code={sampleCode} />);
    expect(screen.getByText("Diagram")).toBeInTheDocument();
  });

  it("shows the code in the code section", () => {
    render(<MermaidDiagram code={sampleCode} />);
    expect(screen.getByText(sampleCode)).toBeInTheDocument();
  });

  it("toggles expansion when the expand/collapse button is clicked", () => {
    render(<MermaidDiagram code={sampleCode} />);
    
    // Initially expanded
    expect(screen.getByText("[Mermaid diagram would render here]")).toBeInTheDocument();
    
    // Click to collapse
    fireEvent.click(screen.getByLabelText("Collapse diagram"));
    
    // Should be collapsed now
    expect(screen.queryByText("[Mermaid diagram would render here]")).not.toBeInTheDocument();
    
    // Click to expand again
    fireEvent.click(screen.getByLabelText("Expand diagram"));
    
    // Should be expanded again
    expect(screen.getByText("[Mermaid diagram would render here]")).toBeInTheDocument();
  });

  it("copies code to clipboard when copy button is clicked", async () => {
    render(<MermaidDiagram code={sampleCode} />);
    
    // Hover to show the copy button
    fireEvent.mouseEnter(screen.getByText("Diagram").closest(".mermaid-diagram-container")!);
    
    // Find and click the copy button
    const copyButton = screen.getByRole("button", { name: /copy/i });
    fireEvent.click(copyButton);
    
    // Check if clipboard.writeText was called with the correct code
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(sampleCode);
  });

  it("displays an error message when there's an error in the Mermaid syntax", () => {
    const errorCode = `graph TD ERROR_PLACEHOLDER
      A --> B`;
    
    render(<MermaidDiagram code={errorCode} />);
    
    expect(screen.getByText("Invalid Mermaid syntax")).toBeInTheDocument();
  });
});