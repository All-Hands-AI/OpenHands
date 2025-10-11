import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import {
  ActionEvent,
  BrowserClickAction,
  BrowserNavigateAction,
  ExecuteBashAction,
  FinishAction,
  MCPToolAction,
  StrReplaceEditorAction,
  TaskTrackerAction,
  ThinkAction,
} from "#/types/v1/core";

const getWriteActionContent = (
  event: ActionEvent<StrReplaceEditorAction>,
): string => {
  let newStr = event.action.new_str;
  if (newStr && newStr.length > MAX_CONTENT_LENGTH) {
    newStr = `${newStr.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `${event.action.path}\n${newStr}`;
};

const getRunActionContent = (event: ActionEvent<ExecuteBashAction>): string =>
  `Command:\n\`${event.action.command}\``;

const getBrowseActionContent = (
  event: ActionEvent<BrowserNavigateAction>,
): string => `Browsing ${event.action.url}`;

const getBrowseInteractiveActionContent = (
  event: ActionEvent<BrowserClickAction>,
) => `**Action:**\n\n\`\`\`python\n${event.action.new_tab}\n\`\`\``;

const getMcpActionContent = (event: ActionEvent<MCPToolAction>): string => {
  // Format MCP action with name and arguments
  const name = event.action.data.name || "";
  const args = event.action.data.arguments || {};
  let details = `**MCP Tool Call:** ${name}\n\n`;
  // Include thought if available
  if (event.thought) {
    details += `\n\n**Thought:**\n${event.thought}`;
  }
  details += `\n\n**Arguments:**\n\`\`\`json\n${JSON.stringify(args, null, 2)}\n\`\`\``;
  return details;
};

const getThinkActionContent = (event: ActionEvent<ThinkAction>): string =>
  event.action.thought;

const getFinishActionContent = (event: ActionEvent<FinishAction>): string =>
  event.action.message.trim();

const getTaskTrackingActionContent = (
  event: ActionEvent<TaskTrackerAction>,
): string => {
  let content = `**Command:** \`${event.action.command}\``;

  if (
    event.action.command === "plan" &&
    event.action.task_list &&
    event.action.task_list.length > 0
  ) {
    content += `\n\n**Task List (${event.action.task_list.length} ${event.action.task_list.length === 1 ? "item" : "items"}):**\n`;

    event.action.task_list.forEach((task, index) => {
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
  } else if (event.action.command === "plan") {
    content += "\n\n**Task List:** Empty";
  }

  return content;
};

// TODO: Extend for the rest of browser actions
export const getActionContent = (event: ActionEvent): string => {
  switch (event.action.kind) {
    case "StrReplaceEditorAction":
      return getWriteActionContent(
        event as ActionEvent<StrReplaceEditorAction>,
      );
    case "ExecuteBashAction":
      return getRunActionContent(event as ActionEvent<ExecuteBashAction>);
    case "BrowserNavigateAction":
      return getBrowseActionContent(
        event as ActionEvent<BrowserNavigateAction>,
      );
    case "BrowserClickAction":
      return getBrowseInteractiveActionContent(
        event as ActionEvent<BrowserClickAction>,
      );
    case "MCPToolAction":
      return getMcpActionContent(event as ActionEvent<MCPToolAction>);
    case "ThinkAction":
      return getThinkActionContent(event as ActionEvent<ThinkAction>);
    case "FinishAction":
      return getFinishActionContent(event as ActionEvent<FinishAction>);
    case "TaskTrackerAction":
      return getTaskTrackingActionContent(
        event as ActionEvent<TaskTrackerAction>,
      );
    default:
      return getDefaultEventContent(event);
  }
};
