import { Trans } from "react-i18next";
import { OpenHandsAction } from "#/types/core/actions";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { MonoComponent } from "./mono-component";
import { PathComponent } from "./path-component";

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

const getActionContent = (event: OpenHandsAction) => {
  let details = "";

  switch (event.action) {
    case "read":
    case "edit":
      break;
    case "write":
      if (event.args.content.length > MAX_CONTENT_LENGTH) {
        details = `${event.args.content.slice(0, MAX_CONTENT_LENGTH)}...`;
      }
      details = `${event.args.path}\n${event.args.content}`;
      break;
    case "run":
      details = `Command:\n\`${event.args.command}\``;
      break;
    case "run_ipython":
      details = `\`\`\`\n${event.args.code}\n\`\`\``;
      break;
    case "browse":
      details = `Browsing ${event.args.url}`;
      break;
    case "browse_interactive":
      details = `**Action:**\n\n\`\`\`python\n${event.args.browser_actions}\n\`\`\``;
      break;
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
      break;
    }
    case "think":
      details = event.args.thought;
      break;
    default:
      details = `\`\`\`\n${JSON.stringify(event.args, null, 2)}\n\`\`\``;
      break;
  }

  const translation = (
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

  return {
    title: translation,
    details,
  };
};

const getObservationContent = (event: OpenHandsObservation) => {
  const content: { title: React.ReactNode; details: string } = {
    title: "",
    details: "",
  };

  switch (event.observation) {
    case "read":
    case "edit":
    case "write":
      content.title = (
        <Trans
          i18nKey={`OBSERVATION_MESSAGE$${event.observation.toUpperCase()}`}
          values={{
            path: event.extras.path,
          }}
          components={{
            path: <PathComponent />,
          }}
        />
      );

      content.details = `Content here`;
      break;
    case "run":
      content.title = (
        <Trans
          i18nKey="OBSERVATION_MESSAGE$RUN"
          values={{
            command: trimText(event.extras.command, 80),
          }}
          components={{
            cmd: <MonoComponent />,
          }}
        />
      );

      content.details = `Command:\n\`${event.extras.command}\`\n\nOutput:\n\`\`\`\n${event.content || "[Command finished execution with no output]"}\n\`\`\``;
      break;
    default:
      content.title = event.observation;
      content.details = `\`\`\`\n${JSON.stringify(event.extras, null, 2)}\n\`\`\``;
      break;
  }

  return content;
};

export const getEventContent = (
  event: OpenHandsAction | OpenHandsObservation,
) => {
  if (isOpenHandsAction(event)) {
    return getActionContent(event);
  }
  if (isOpenHandsObservation(event)) {
    return getObservationContent(event);
  }
  return { title: "Unknown event", details: "Unknown event" };
};

export const isSuccessObservation = (event: OpenHandsObservation) => {
  const hasContent = event.content.length > 0;

  switch (event.observation) {
    case "run":
      return event.extras.metadata.exit_code === 0;
    case "run_ipython":
      return !event.content.toLowerCase().includes("error:");
    case "read":
    case "edit":
    case "mcp":
      if (!hasContent) return false;
      return !event.content.toLowerCase().includes("error:");
    default:
      return true;
  }
};
