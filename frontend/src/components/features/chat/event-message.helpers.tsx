import { Trans } from "react-i18next";
import { OpenHandsAction } from "#/types/core/actions";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { MonoComponent } from "./mono-component";
import { PathComponent } from "./path-component";

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

const hasPathProperty = (
  obj: Record<string, unknown>,
): obj is { path: string } => typeof obj.path === "string";

const hasCommandProperty = (
  obj: Record<string, unknown>,
): obj is { command: string } => typeof obj.command === "string";

const MAX_CONTENT_LENGTH = 1000;

const trimText = (text: string, maxLength: number): string => {
  if (!text) return "";
  return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

const getActionContent = (event: OpenHandsAction): string => {
  let details = "";

  switch (event.action) {
    case "read":
    case "edit":
      return "";
    case "write": {
      let { content } = event.args;
      if (content.length > MAX_CONTENT_LENGTH) {
        content = `${event.args.content.slice(0, MAX_CONTENT_LENGTH)}...`;
      }
      return `${event.args.path}\n${content}`;
    }
    case "run":
      return `Command:\n\`${event.args.command}\``;
    case "run_ipython":
      return `\`\`\`\n${event.args.code}\n\`\`\``;
    case "browse":
      return `Browsing ${event.args.url}`;
    case "browse_interactive":
      return `**Action:**\n\n\`\`\`python\n${event.args.browser_actions}\n\`\`\``;
    case "call_tool_mcp": {
      // Format MCP action with name and arguments
      const name = event.args.name || "";
      const args = event.args.arguments || {};
      details = `**MCP Tool Call:** ${name}\n\n`;
      // Include thought if available
      if (event.args.thought) {
        details += `\n\n**Thought:**\n${event.args.thought}`;
      }
      details += `\n\n**Arguments:**\n\`\`\`json\n${JSON.stringify(args, null, 2)}\n\`\`\``;
      return details;
    }
    case "think":
      return event.args.thought;
    default:
      return `\`\`\`\n${JSON.stringify(event.args, null, 2)}\n\`\`\``;
  }
};

const getObservationContent = (event: OpenHandsObservation): string => {
  switch (event.observation) {
    case "read":
      return `\`\`\`\n${event.content}\n\`\`\``; // Content is already truncated by the ACI
    case "edit":
      if (isSuccessObservation(event)) {
        return `\`\`\`diff\n${event.extras.diff}\n\`\`\``; // Content is already truncated by the ACI
      }
      return event.content;
    case "write":
      return `Content here`;
    case "run":
      return `Command:\n\`${event.extras.command}\`\n\nOutput:\n\`\`\`sh\n${event.content || "[Command finished execution with no output]"}\n\`\`\``;
    case "browse": {
      let contentDetails = `**URL:** ${event.extras.url}\n`;
      if (event.extras.error) {
        contentDetails += `\n\n**Error:**\n${event.extras.error}\n`;
      }
      contentDetails += `\n\n**Output:**\n${event.content}`;
      if (contentDetails.length > MAX_CONTENT_LENGTH) {
        contentDetails = `${contentDetails.slice(0, MAX_CONTENT_LENGTH)}...(truncated)`;
      }
      return contentDetails;
    }
    case "mcp":
      return `**Output:**\n\`\`\`\n${event.content.trim() || "[MCP Tool finished execution with no output]"}\n\`\`\``;
    default:
      return `\`\`\`\n${JSON.stringify(event.extras, null, 2)}\n\`\`\``;
  }
};

export const getEventContent = (
  event: OpenHandsAction | OpenHandsObservation,
) => {
  let title: React.ReactNode = "";
  let details: string = "";

  if (isOpenHandsAction(event)) {
    title = (
      <Trans
        i18nKey={`ACTION_MESSAGE$${event.action.toUpperCase()}`}
        values={{
          path: hasPathProperty(event.args) && event.args.path,
          command:
            hasCommandProperty(event.args) && trimText(event.args.command, 80),
        }}
        components={{
          path: <PathComponent />,
          cmd: <MonoComponent />,
        }}
      />
    );
    details = getActionContent(event);
  }

  if (isOpenHandsObservation(event)) {
    title = (
      <Trans
        i18nKey={`OBSERVATION_MESSAGE$${event.observation.toUpperCase()}`}
        values={{
          path: hasPathProperty(event.extras) && event.extras.path,
          command:
            hasCommandProperty(event.extras) &&
            trimText(event.extras.command, 80),
        }}
        components={{
          path: <PathComponent />,
          cmd: <MonoComponent />,
        }}
      />
    );
    details = getObservationContent(event);
  }

  return {
    title: title ?? "Unknown event",
    details: details ?? "Unknown event",
  };
};
