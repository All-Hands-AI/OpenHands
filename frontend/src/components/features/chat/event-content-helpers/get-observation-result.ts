import { OpenHandsObservation } from "#/types/core/observations";

export type ObservationResultStatus = "success" | "error" | "timeout";

export const getObservationResult = (event: OpenHandsObservation) => {
  const hasContent = event.content.length > 0;
  const contentIncludesError = event.content.toLowerCase().includes("error:");

  switch (event.observation) {
    case "run": {
      const exitCode = event.extras.metadata.exit_code;

      if (exitCode === -1) return "timeout"; // Command timed out
      if (exitCode === 0) return "success"; // Command executed successfully
      return "error"; // Command failed
    }
    case "run_ipython":
    case "read":
    case "edit":
    case "mcp":
      if (!hasContent || contentIncludesError) return "error";
      return "success"; // Content is valid
    default:
      return "success";
  }
};
