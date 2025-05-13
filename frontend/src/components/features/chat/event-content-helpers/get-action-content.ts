import {
  FileWriteAction,
  CommandAction,
  IPythonAction,
  BrowseAction,
  BrowseInteractiveAction,
  MCPAction,
  ThinkAction,
  OpenHandsAction,
} from "#/types/core/actions";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";

const getWriteActionContent = (event: FileWriteAction): string => {
  let { content } = event.args;
  if (content.length > MAX_CONTENT_LENGTH) {
    content = `${event.args.content.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `${event.args.path}\n${content}`;
};

const getRunActionContent = (event: CommandAction): string =>
  `Command:\n\`${event.args.command}\``;

const getIPythonActionContent = (event: IPythonAction): string =>
  `\`\`\`\n${event.args.code}\n\`\`\``;

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
    default:
      return getDefaultEventContent(event);
  }
};
