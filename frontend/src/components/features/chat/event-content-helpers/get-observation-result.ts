import { ObservationEvent } from "#/types/v1/core";

export type ObservationResultStatus = "success" | "error" | "timeout";

export const getObservationResult = (event: ObservationEvent) => {
  const hasContent = event.observation.content.length > 0;
  const contentIncludesError = event.content.toLowerCase().includes("error:");

  switch (event.observation.kind) {
    case "ExecuteBashObservation": {
      const exitCode = event.observation.metadata.exit_code;

      if (exitCode === -1) return "timeout"; // Command timed out
      if (exitCode === 0) return "success"; // Command executed successfully
      return "error"; // Command failed
    }
    case "StrReplaceEditorObservation":
    case "MCPToolObservation":
      if (!hasContent || contentIncludesError) return "error";
      return "success"; // Content is valid
    default:
      return "success";
  }
};
