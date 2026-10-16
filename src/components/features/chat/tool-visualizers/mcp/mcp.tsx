import React from "react";
import { MarkdownRenderer } from "#/components/features/markdown/markdown-renderer";
import { MCPAppArtifact } from "#/components/features/mcp-apps/mcp-app-artifact";
import { getObservationContent } from "#/components/conversation-events/chat/event-content-helpers/get-observation-content";
import type { ObservationEvent } from "#/types/agent-server/core";
import type { MCPToolObservation } from "#/types/agent-server/core/base/observation";
import type { MCPAppDescriptor } from "#/types/mcp-app";

// @spec MCA-001 — App results retain the original MCP text alongside the artifact.
export function MCPBody({
  observation,
  descriptor,
}: {
  observation: ObservationEvent<MCPToolObservation>;
  descriptor: MCPAppDescriptor;
}) {
  return (
    <>
      <MarkdownRenderer>{getObservationContent(observation)}</MarkdownRenderer>
      <MCPAppArtifact event={observation} descriptor={descriptor} />
    </>
  );
}
