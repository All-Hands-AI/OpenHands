import React, { useState, useEffect, useRef } from "react";
import { cn } from "#/utils/utils";
import { CopyToClipboardButton } from "#/components/shared/buttons/copy-to-clipboard-button";
import { ChevronDown, ChevronUp } from "lucide-react";
import mermaid from "mermaid";
import { initializeMermaid } from "#/utils/mermaid-init";

// Initialize mermaid when this component is first imported
initializeMermaid();

interface MermaidDiagramProps {
  code: string;
  className?: string;
}

/**
 * Component to render Mermaid diagrams.
 * Uses the mermaid library to render diagrams from text notation.
 */
export function MermaidDiagram({ code, className }: MermaidDiagramProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isCopied, setIsCopied] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [svg, setSvg] = useState<string>("");
  const mermaidRef = useRef<HTMLDivElement>(null);
  const uniqueId = useRef(`mermaid-${Math.random().toString(36).substring(2, 11)}`);

  // Render the mermaid diagram
  useEffect(() => {
    if (!isExpanded || !code) return;

    const renderDiagram = async () => {
      try {
        // Reset error state
        setError(null);
        
        // Generate SVG
        const { svg } = await mermaid.render(uniqueId.current, code);
        setSvg(svg);
      } catch (err) {
        console.error("Mermaid rendering error:", err);
        setError(err instanceof Error ? err.message : "Failed to render diagram");
      }
    };

    renderDiagram();
  }, [code, isExpanded]);

  const handleCopyToClipboard = async () => {
    await navigator.clipboard.writeText(code);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div 
      className={cn(
        "mermaid-diagram-container rounded-lg border border-gray-200 dark:border-gray-700 my-4",
        className
      )}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className="mermaid-header flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded-t-lg">
        <div className="flex items-center">
          <button 
            onClick={toggleExpand}
            className="mr-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            aria-label={isExpanded ? "Collapse diagram" : "Expand diagram"}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          <span className="font-medium">Diagram</span>
        </div>
        <CopyToClipboardButton
          isHidden={!isHovering}
          isDisabled={isCopied}
          onClick={handleCopyToClipboard}
          mode={isCopied ? "copied" : "copy"}
        />
      </div>
      
      {isExpanded && (
        <div className="mermaid-content p-4">
          {error ? (
            <div className="text-red-500 p-2 bg-red-50 dark:bg-red-900/20 rounded">
              {error}
            </div>
          ) : (
            <>
              <div className="mermaid-render bg-white dark:bg-gray-900 p-4 rounded mb-2">
                {svg ? (
                  <div 
                    className="flex justify-center"
                    dangerouslySetInnerHTML={{ __html: svg }} 
                  />
                ) : (
                  <div className="text-center text-gray-500 dark:text-gray-400 p-4">
                    Loading diagram...
                  </div>
                )}
              </div>
              <div className="mermaid-code bg-gray-50 dark:bg-gray-800 p-2 rounded text-sm font-mono overflow-auto">
                {code}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}