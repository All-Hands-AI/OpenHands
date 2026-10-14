import React from "react";
import {
  OpenHandsEvent,
  ActionEvent,
  ObservationEvent,
} from "#/types/agent-server/core";
import {
  isActionEvent,
  isObservationEvent,
} from "#/types/agent-server/type-guards";
import { actionVisualizers, observationVisualizers } from "./index";
import type { MCPToolObservation } from "#/types/agent-server/core/base/observation";
import type { MCPAppDescriptor } from "#/types/mcp-app";
import { MCPBody } from "./mcp/mcp";

/**
 * Returns the React body for an action/observation event when a tool visualizer
 * is registered for its `kind`, or `null` to tell the caller to fall back to
 * the markdown pipeline. Only the collapsible details body is produced here —
 * the title pipeline, success indicator, and ACP path are untouched.
 *
 * `correspondingAction` is the action an observation responds to (when it can
 * be resolved); it lets observation cards reuse action-side fields such as a
 * file view range.
 */
export function resolveVisualizerBody(
  event: OpenHandsEvent,
  correspondingAction?: ActionEvent,
  mcpAppDescriptor?: MCPAppDescriptor | null,
): React.ReactNode | null {
  if (isActionEvent(event)) {
    const visualizer = actionVisualizers.get(event.action.kind);
    if (visualizer) {
      return <visualizer.Body action={event} />;
    }
  } else if (isObservationEvent(event)) {
    // @spec MCA-001 — Plain MCP observations keep the existing markdown path.
    if (event.observation.kind === "MCPToolObservation") {
      return mcpAppDescriptor ? (
        <MCPBody
          observation={event as ObservationEvent<MCPToolObservation>}
          descriptor={mcpAppDescriptor}
        />
      ) : null;
    }
    const visualizer = observationVisualizers.get(event.observation.kind);
    if (visualizer) {
      return (
        <visualizer.Body action={correspondingAction} observation={event} />
      );
    }
  }
  return null;
}
