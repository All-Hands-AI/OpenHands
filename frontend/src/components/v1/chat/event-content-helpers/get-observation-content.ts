import { ObservationEvent } from "#/types/v1/core";
import { getObservationResult } from "./get-observation-result";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import i18n from "#/i18n";

// File Editor Observations
const getFileEditorObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have required properties
  if (!("command" in observation && "output" in observation)) {
    return "";
  }

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
const getExecuteBashObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have output property
  if (!("output" in observation)) {
    return "";
  }

  let { output } = observation;

  if (output.length > MAX_CONTENT_LENGTH) {
    output = `${output.slice(0, MAX_CONTENT_LENGTH)}...`;
  }

  return `Output:\n\`\`\`sh\n${output.trim() || i18n.t("OBSERVATION$COMMAND_NO_OUTPUT")}\n\`\`\``;
};

// Tool Observations
const getBrowserObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have required properties
  if (!("output" in observation)) {
    return "";
  }

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

const getMCPToolObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have required properties
  if (
    !(
      "content" in observation &&
      "tool_name" in observation &&
      "is_error" in observation
    )
  ) {
    return "";
  }

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
const getTaskTrackerObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have required properties
  if (!("command" in observation && "task_list" in observation)) {
    return "";
  }

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
const getThinkObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have content property
  if (!("content" in observation)) {
    return "";
  }

  // Type guard: ThinkObservation.content is always a string
  if (typeof observation.content === "string") {
    return observation.content || "";
  }

  // If it's an array (from MCPToolObservation), return empty string
  return "";
};

const getFinishObservationContent = (event: ObservationEvent): string => {
  const { observation } = event;

  // Early return if observation doesn't have message property
  if (!("message" in observation)) {
    return "";
  }

  return observation.message || "";
};

export const getObservationContent = (event: ObservationEvent): string => {
  const observationType = event.observation.kind;

  switch (observationType) {
    case "FileEditorObservation":
    case "StrReplaceEditorObservation":
      return getFileEditorObservationContent(event);

    case "ExecuteBashObservation":
      return getExecuteBashObservationContent(event);

    case "BrowserObservation":
      return getBrowserObservationContent(event);

    case "MCPToolObservation":
      return getMCPToolObservationContent(event);

    case "TaskTrackerObservation":
      return getTaskTrackerObservationContent(event);

    case "ThinkObservation":
      return getThinkObservationContent(event);

    case "FinishObservation":
      return getFinishObservationContent(event);

    default:
      return getDefaultEventContent(event);
  }
};
