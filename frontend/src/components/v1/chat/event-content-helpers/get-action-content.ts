import { ActionEvent } from "#/types/v1/core";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import i18n from "#/i18n";
import { SecurityRisk } from "#/types/v1/core/base/common";
import {
  ExecuteBashAction,
  FileEditorAction,
  StrReplaceEditorAction,
  MCPToolAction,
  ThinkAction,
  FinishAction,
  TaskTrackerAction,
  BrowserNavigateAction,
  BrowserClickAction,
  BrowserTypeAction,
  BrowserGetStateAction,
  BrowserGetContentAction,
  BrowserScrollAction,
  BrowserGoBackAction,
  BrowserListTabsAction,
  BrowserSwitchTabAction,
  BrowserCloseTabAction,
} from "#/types/v1/core/base/action";

const getRiskText = (risk: SecurityRisk) => {
  switch (risk) {
    case SecurityRisk.LOW:
      return i18n.t("SECURITY$LOW_RISK");
    case SecurityRisk.MEDIUM:
      return i18n.t("SECURITY$MEDIUM_RISK");
    case SecurityRisk.HIGH:
      return i18n.t("SECURITY$HIGH_RISK");
    case SecurityRisk.UNKNOWN:
    default:
      return i18n.t("SECURITY$UNKNOWN_RISK");
  }
};

const getNoContentActionContent = (): string => "";

// File Editor Actions
const getFileEditorActionContent = (
  action: FileEditorAction | StrReplaceEditorAction,
): string => {
  // Early return if not a create command or no file text
  if (action.command !== "create" || !action.file_text) {
    return getNoContentActionContent();
  }

  // Process file text with length truncation
  let fileText = action.file_text;
  if (fileText.length > MAX_CONTENT_LENGTH) {
    fileText = `${fileText.slice(0, MAX_CONTENT_LENGTH)}...`;
  }

  return `${action.path}\n${fileText}`;
};

// Command Actions
const getExecuteBashActionContent = (
  event: ActionEvent<ExecuteBashAction>,
): string => {
  let content = `Command:\n\`${event.action.command}\``;

  // Add security risk information if it's HIGH or MEDIUM
  if (
    event.security_risk === SecurityRisk.HIGH ||
    event.security_risk === SecurityRisk.MEDIUM
  ) {
    content += `\n\n${getRiskText(event.security_risk)}`;
  }

  return content;
};

// Tool Actions
const getMCPToolActionContent = (action: MCPToolAction): string => {
  // For V1, the tool name is in the event's tool_name property, not in the action
  let details = `**MCP Tool Call**\n\n`;
  details += `**Arguments:**\n\`\`\`json\n${JSON.stringify(action.data, null, 2)}\n\`\`\``;
  return details;
};

// Simple Actions
const getThinkActionContent = (action: ThinkAction): string => action.thought;

const getFinishActionContent = (action: FinishAction): string =>
  action.message.trim();

// Complex Actions
const getTaskTrackerActionContent = (action: TaskTrackerAction): string => {
  let content = `**Command:** \`${action.command}\``;

  // Handle plan command with task list
  if (action.command === "plan") {
    if (action.task_list && action.task_list.length > 0) {
      content += `\n\n**Task List (${action.task_list.length} ${action.task_list.length === 1 ? "item" : "items"}):**\n`;
      action.task_list.forEach((task, index: number) => {
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
    } else {
      content += "\n\n**Task List:** Empty";
    }
  }

  return content;
};

// Browser Actions
type BrowserAction =
  | BrowserNavigateAction
  | BrowserClickAction
  | BrowserTypeAction
  | BrowserGetStateAction
  | BrowserGetContentAction
  | BrowserScrollAction
  | BrowserGoBackAction
  | BrowserListTabsAction
  | BrowserSwitchTabAction
  | BrowserCloseTabAction;

const getBrowserActionContent = (action: BrowserAction): string => {
  switch (action.kind) {
    case "BrowserNavigateAction":
      if ("url" in action) {
        return `Browsing ${action.url}`;
      }
      break;
    case "BrowserClickAction":
    case "BrowserTypeAction":
    case "BrowserGetStateAction":
    case "BrowserGetContentAction":
    case "BrowserScrollAction":
    case "BrowserGoBackAction":
    case "BrowserListTabsAction":
    case "BrowserSwitchTabAction":
    case "BrowserCloseTabAction":
      // These browser actions typically don't need detailed content display
      return getNoContentActionContent();
    default:
      return getNoContentActionContent();
  }

  return getNoContentActionContent();
};

export const getActionContent = (event: ActionEvent): string => {
  const { action } = event;
  const actionType = action.kind;

  switch (actionType) {
    case "FileEditorAction":
    case "StrReplaceEditorAction":
      return getFileEditorActionContent(action);

    case "ExecuteBashAction":
      return getExecuteBashActionContent(
        event as ActionEvent<ExecuteBashAction>,
      );

    case "MCPToolAction":
      return getMCPToolActionContent(action);

    case "ThinkAction":
      return getThinkActionContent(action);

    case "FinishAction":
      return getFinishActionContent(action);

    case "TaskTrackerAction":
      return getTaskTrackerActionContent(action);

    case "BrowserNavigateAction":
    case "BrowserClickAction":
    case "BrowserTypeAction":
    case "BrowserGetStateAction":
    case "BrowserGetContentAction":
    case "BrowserScrollAction":
    case "BrowserGoBackAction":
    case "BrowserListTabsAction":
    case "BrowserSwitchTabAction":
    case "BrowserCloseTabAction":
      return getBrowserActionContent(action);

    default:
      return getDefaultEventContent(event);
  }
};
