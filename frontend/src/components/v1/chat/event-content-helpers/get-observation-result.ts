import { ObservationEvent } from "#/types/v1/core";

export type ObservationResultStatus = "success" | "error" | "timeout";

export const getObservationResult = (
  event: ObservationEvent,
): ObservationResultStatus => {
  const { observation } = event;
  const observationType = observation.kind;

  switch (observationType) {
    case "ExecuteBashObservation": {
      const exitCode = observation.exit_code;

      if (exitCode === -1) return "timeout"; // Command timed out
      if (exitCode === 0) return "success"; // Command executed successfully
      return "error"; // Command failed
    }
    case "FileEditorObservation":
    case "StrReplaceEditorObservation":
      // Check if there's an error
      if (observation.error) return "error";
      return "success";
    case "MCPToolObservation":
      if (observation.is_error) return "error";
      return "success";
    default:
      return "success";
  }
};
