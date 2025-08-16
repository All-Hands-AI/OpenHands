import { ActionSecurityRisk } from "#/state/security-analyzer-slice";
import {
  FileWriteAction,
  CommandAction,
  IPythonAction,
  BrowseAction,
  BrowseInteractiveAction,
  MCPAction,
  ThinkAction,
  OpenHandsAction,
  FinishAction,
  TaskTrackingAction,
} from "#/types/core/actions";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import i18n from "#/i18n";

const getRiskText = (risk: ActionSecurityRisk | string | number) => {
  // Debug logging to see what risk value we're getting
  console.log("getRiskText called with risk:", risk, "type:", typeof risk);
  console.log("ActionSecurityRisk enum values:", {
    UNKNOWN: ActionSecurityRisk.UNKNOWN,
    LOW: ActionSecurityRisk.LOW,
    MEDIUM: ActionSecurityRisk.MEDIUM,
    HIGH: ActionSecurityRisk.HIGH,
  });
  
  // Handle string values that might come from backend
  if (typeof risk === "string") {
    const lowerRisk = risk.toLowerCase();
    if (lowerRisk === "low") return i18n.t("SECURITY$LOW_RISK");
    if (lowerRisk === "medium") return i18n.t("SECURITY$MEDIUM_RISK");
    if (lowerRisk === "high") return i18n.t("SECURITY$HIGH_RISK");
    return i18n.t("SECURITY$UNKNOWN_RISK");
  }
  
  // Handle numeric values
  const numericRisk = Number(risk);
  switch (numericRisk) {
    case ActionSecurityRisk.LOW:
      return i18n.t("SECURITY$LOW_RISK");
    case ActionSecurityRisk.MEDIUM:
      return i18n.t("SECURITY$MEDIUM_RISK");
    case ActionSecurityRisk.HIGH:
      return i18n.t("SECURITY$HIGH_RISK");
    case ActionSecurityRisk.UNKNOWN:
    default:
      return i18n.t("SECURITY$UNKNOWN_RISK");
  }
};

const getWriteActionContent = (event: FileWriteAction): string => {
  let { content } = event.args;
  if (content.length > MAX_CONTENT_LENGTH) {
    content = `${event.args.content.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `${event.args.path}\n${content}`;
};

const getRunActionContent = (event: CommandAction): string => {
  let content = `Command:\n\`${event.args.command}\``;

  if (event.args.confirmation_state === "awaiting_confirmation") {
    content += `\n\n${getRiskText(event.args.security_risk)}`;
  }

  return content;
};

const getIPythonActionContent = (event: IPythonAction): string => {
  let content = `\`\`\`\n${event.args.code}\n\`\`\``;

  if (event.args.confirmation_state === "awaiting_confirmation") {
    content += `\n\n${getRiskText(event.args.security_risk)}`;
  }

  return content;
};

const getBrowseActionContent = (event: BrowseAction): string =>
  `Browsing ${event.args.url}`;

const getBrowseInteractiveActionContent = (event: BrowseInteractiveAction) =>
  `**Action:**\n\n\`\`\`python\n${event.args.browser_actions}\n\`\`\``;

const getMcpActionContent = (event: MCPAction): string => {
  // Format MCP action with name and arguments
  const name = event.args.name || "";
  const args = event.args.arguments || {};
  let details = `**MCP Tool Call:** ${name}\n\n`;
  // Include thought if available
  if (event.args.thought) {
    details += `\n\n**Thought:**\n${event.args.thought}`;
  }
  details += `\n\n**Arguments:**\n\`\`\`json\n${JSON.stringify(args, null, 2)}\n\`\`\``;
  return details;
};

const getThinkActionContent = (event: ThinkAction): string =>
  event.args.thought;

const getFinishActionContent = (event: FinishAction): string =>
  event.args.final_thought.trim();

const getTaskTrackingActionContent = (event: TaskTrackingAction): string => {
  let content = `**Command:** \`${event.args.command}\``;

  if (
    event.args.command === "plan" &&
    event.args.task_list &&
    event.args.task_list.length > 0
  ) {
    content += `\n\n**Task List (${event.args.task_list.length} ${event.args.task_list.length === 1 ? "item" : "items"}):**\n`;

    event.args.task_list.forEach((task, index) => {
      const statusIcon =
        {
          todo: "⏳",
          in_progress: "🔄",
          done: "✅",
        }[task.status] || "❓";

      content += `\n${index + 1}. ${statusIcon} **[${task.status.toUpperCase().replace("_", " ")}]** ${task.title}`;
      content += `\n   *ID: ${task.id}*`;
      if (task.notes) {
        content += `\n   *Notes: ${task.notes}*`;
      }
    });
  } else if (event.args.command === "plan") {
    content += "\n\n**Task List:** Empty";
  }

  return content;
};

const getNoContentActionContent = (): string => "";

export const getActionContent = (event: OpenHandsAction): string => {
  switch (event.action) {
    case "read":
    case "edit":
      return getNoContentActionContent();
    case "write":
      return getWriteActionContent(event);
    case "run":
      return getRunActionContent(event);
    case "run_ipython":
      return getIPythonActionContent(event);
    case "browse":
      return getBrowseActionContent(event);
    case "browse_interactive":
      return getBrowseInteractiveActionContent(event);
    case "call_tool_mcp":
      return getMcpActionContent(event);
    case "think":
      return getThinkActionContent(event);
    case "finish":
      return getFinishActionContent(event);
    case "task_tracking":
      return getTaskTrackingActionContent(event);
    default:
      return getDefaultEventContent(event);
  }
};
