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
} from "#/types/core/actions";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";

const getRiskText = (risk: ActionSecurityRisk) => {
  switch (risk) {
    case ActionSecurityRisk.LOW:
      return "Low Risk";
    case ActionSecurityRisk.MEDIUM:
      return "Medium Risk";
    case ActionSecurityRisk.HIGH:
      return "High Risk";
    case ActionSecurityRisk.UNKNOWN:
    default:
      return "Unknown Risk";
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

const getFinishActionContent = (event: FinishAction): string => {
  let content = event.args.final_thought;

  switch (event.args.task_completed) {
    case "success":
      content +=
        "\n\n\nI believe that the task was **completed successfully**.";
      break;
    case "failure":
      content += "\n\n\nI believe that the task was **not completed**.";
      break;
    case "partial":
    default:
      content += "\n\n\nI believe that the task was **completed partially**.";
      break;
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
    default:
      return getDefaultEventContent(event);
  }
};
