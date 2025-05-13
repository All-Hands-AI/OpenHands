import { OpenHandsObservation } from "#/types/core/observations";

export const isSuccessObservation = (event: OpenHandsObservation) => {
  const hasContent = event.content.length > 0;

  switch (event.observation) {
    case "run":
      return event.extras.metadata.exit_code === 0;
    case "run_ipython":
    case "read":
    case "edit":
    case "mcp":
      if (!hasContent) return false;
      return !event.content.toLowerCase().includes("error:");
    default:
      return true;
  }
};
