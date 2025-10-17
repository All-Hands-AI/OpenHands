import { ObservationEvent } from "#/types/v1/core";
import { getObservationResult } from "./get-observation-result";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import i18n from "#/i18n";
import {
  MCPToolObservation,
  FinishObservation,
  ThinkObservation,
  BrowserObservation,
  ExecuteBashObservation,
  FileEditorObservation,
  StrReplaceEditorObservation,
  TaskTrackerObservation,
} from "#/types/v1/core/base/observation";

// File Editor Observations
const getFileEditorObservationContent = (
  event: ObservationEvent<FileEditorObservation | StrReplaceEditorObservation>,
): string => {
  const { observation } = event;

  const successMessage = getObservationResult(event) === "success";

  // For view commands or successful edits with content changes, format as code block
  if (
    (successMessage &&
      "old_content" in observation &&
      "new_content" in observation &&
      observation.old_content &&
      observation.new_content) ||
    observation.command === "view"
  ) {
    return `\`\`\`\n${observation.output}\n\`\`\``;
  }

  // For other commands, return the output as-is
  return observation.output;
};

// Command Observations
const getExecuteBashObservationContent = (
  event: ObservationEvent<ExecuteBashObservation>,
): string => {
  const { observation } = event;

  let { output } = observation;

  if (output.length > MAX_CONTENT_LENGTH) {
    output = `${output.slice(0, MAX_CONTENT_LENGTH)}...`;
  }

  return `Output:\n\`\`\`sh\n${output.trim() || i18n.t("OBSERVATION$COMMAND_NO_OUTPUT")}\n\`\`\``;
};

// Tool Observations
const getBrowserObservationContent = (
  event: ObservationEvent<BrowserObservation>,
): string => {
  const { observation } = event;

  let contentDetails = "";

  if ("error" in observation && observation.error) {
    contentDetails += `**Error:**\n${observation.error}\n\n`;
  }

  contentDetails += `**Output:**\n${observation.output}`;

  if (contentDetails.length > MAX_CONTENT_LENGTH) {
    contentDetails = `${contentDetails.slice(0, MAX_CONTENT_LENGTH)}...(truncated)`;
  }

  return contentDetails;
};

const getMCPToolObservationContent = (
  event: ObservationEvent<MCPToolObservation>,
): string => {
  const { observation } = event;

  // Extract text content from the observation
  const textContent = observation.content
    .filter((c) => c.type === "text")
    .map((c) => c.text)
    .join("\n");

  let content = `**Tool:** ${observation.tool_name}\n\n`;

  if (observation.is_error) {
    content += `**Error:**\n${textContent}`;
  } else {
    content += `**Result:**\n${textContent}`;
  }

  if (content.length > MAX_CONTENT_LENGTH) {
    content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
  }

  return content;
};

// Complex Observations
const getTaskTrackerObservationContent = (
  event: ObservationEvent<TaskTrackerObservation>,
): string => {
  const { observation } = event;

  const { command, task_list: taskList } = observation;
  let content = `**Command:** \`${command}\``;

  if (command === "plan" && taskList.length > 0) {
    content += `\n\n**Task List (${taskList.length} ${taskList.length === 1 ? "item" : "items"}):**\n`;

    taskList.forEach((task, index: number) => {
      const statusMap = {
        todo: "⏳",
        in_progress: "🔄",
        done: "✅",
      };
      const statusIcon =
        statusMap[task.status as keyof typeof statusMap] || "❓";

      content += `\n${index + 1}. ${statusIcon} **[${task.status.toUpperCase().replace("_", " ")}]** ${task.title}`;
      if (task.notes) {
        content += `\n   *Notes: ${task.notes}*`;
      }
    });
  } else if (command === "plan") {
    content += "\n\n**Task List:** Empty";
  }

  if (
    "content" in observation &&
    observation.content &&
    observation.content.trim()
  ) {
    content += `\n\n**Result:** ${observation.content.trim()}`;
  }

  return content;
};

// Simple Observations
const getThinkObservationContent = (
  event: ObservationEvent<ThinkObservation>,
): string => {
  const { observation } = event;
  return observation.content || "";
};

const getFinishObservationContent = (
  event: ObservationEvent<FinishObservation>,
): string => {
  const { observation } = event;
  return observation.message || "";
};

export const getObservationContent = (event: ObservationEvent): string => {
  const observationType = event.observation.kind;

  switch (observationType) {
    case "FileEditorObservation":
    case "StrReplaceEditorObservation":
      return getFileEditorObservationContent(
        event as ObservationEvent<
          FileEditorObservation | StrReplaceEditorObservation
        >,
      );

    case "ExecuteBashObservation":
      return getExecuteBashObservationContent(
        event as ObservationEvent<ExecuteBashObservation>,
      );

    case "BrowserObservation":
      return getBrowserObservationContent(
        event as ObservationEvent<BrowserObservation>,
      );

    case "MCPToolObservation":
      return getMCPToolObservationContent(
        event as ObservationEvent<MCPToolObservation>,
      );

    case "TaskTrackerObservation":
      return getTaskTrackerObservationContent(
        event as ObservationEvent<TaskTrackerObservation>,
      );

    case "ThinkObservation":
      return getThinkObservationContent(
        event as ObservationEvent<ThinkObservation>,
      );

    case "FinishObservation":
      return getFinishObservationContent(
        event as ObservationEvent<FinishObservation>,
      );

    default:
      return getDefaultEventContent(event);
  }
};
