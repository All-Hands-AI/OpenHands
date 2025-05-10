import React from "react";
import { MermaidDemo } from "#/components/features/mermaid";

/**
 * Demo page for showcasing the Mermaid diagram functionality.
 * This page can be used to test and demonstrate the Mermaid diagram rendering.
 */
export default function MermaidDemoRoute() {
  return (
    <div className="container mx-auto py-8">
      <MermaidDemo />
    </div>
  );
}