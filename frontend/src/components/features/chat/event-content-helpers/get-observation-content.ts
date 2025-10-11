import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import i18n from "#/i18n";
import {
  BrowserObservation,
  ExecuteBashObservation,
  ObservationEvent,
  StrReplaceEditorObservation,
  TaskTrackerObservation,
} from "#/types/v1/core";

const getReadObservationContent = (
  event: ObservationEvent<StrReplaceEditorObservation>,
): string => `\`\`\`\n${event.observation.new_content}\n\`\`\``;

const getCommandObservationContent = (
  event: ObservationEvent<ExecuteBashObservation>,
): string => {
  let { command } = event.observation;
  if (command && command.length > MAX_CONTENT_LENGTH) {
    command = `${command.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `Output:\n\`\`\`sh\n${command?.trim() || i18n.t("OBSERVATION$COMMAND_NO_OUTPUT")}\n\`\`\``;
};

const getBrowseObservationContent = (
  event: ObservationEvent<BrowserObservation>,
) => {
  let contentDetails = `**URL:** ${event.observation.url}\n`;
  if (event.observation.error) {
    contentDetails += `\n\n**Error:**\n${event.observation.error}\n`;
  }
  contentDetails += `\n\n**Output:**\n${event.observation.output}`;
  if (contentDetails.length > MAX_CONTENT_LENGTH) {
    contentDetails = `${contentDetails.slice(0, MAX_CONTENT_LENGTH)}...(truncated)`;
  }
  return contentDetails;
};

const getTaskTrackingObservationContent = (
  event: ObservationEvent<TaskTrackerObservation>,
): string => {
  const { command, task_list: taskList } = event.observation;
  let content = `**Command:** \`${command}\``;

  if (command === "plan" && taskList.length > 0) {
    content += `\n\n**Task List (${taskList.length} ${taskList.length === 1 ? "item" : "items"}):**\n`;

    taskList.forEach((task, index) => {
      const statusIcon =
        {
          todo: "⏳",
          in_progress: "🔄",
          done: "✅",
        }[task.status] || "❓";

      content += `\n${index + 1}. ${statusIcon} **[${task.status.toUpperCase().replace("_", " ")}]** ${task.title}`;
      content += `\n   *ID: ${task.title}*`;
      if (task.notes) {
        content += `\n   *Notes: ${task.notes}*`;
      }
    });
  } else if (command === "plan") {
    content += "\n\n**Task List:** Empty";
  }

  if (event.observation.content && event.observation.content.trim()) {
    content += `\n\n**Result:** ${event.observation.content.trim()}`;
  }

  return content;
};

export const getObservationContent = (event: ObservationEvent): string => {
  switch (event.observation.kind) {
    case "StrReplaceEditorObservation":
      return getReadObservationContent(
        event as ObservationEvent<StrReplaceEditorObservation>,
      );
    case "ExecuteBashObservation":
      return getCommandObservationContent(
        event as ObservationEvent<ExecuteBashObservation>,
      );
    case "BrowserObservation":
      return getBrowseObservationContent(
        event as ObservationEvent<BrowserObservation>,
      );
    case "TaskTrackerObservation":
      return getTaskTrackingObservationContent(
        event as ObservationEvent<TaskTrackerObservation>,
      );
    default:
      return getDefaultEventContent(event);
  }
};
