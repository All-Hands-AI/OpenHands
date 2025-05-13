import {
  ReadObservation,
  CommandObservation,
  IPythonObservation,
  EditObservation,
  BrowseObservation,
  OpenHandsObservation,
} from "#/types/core/observations";
import { isSuccessObservation } from "./is-success-observation";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";

const getReadObservationContent = (event: ReadObservation): string =>
  `\`\`\`\n${event.content}\n\`\`\``;

const getCommandObservationContent = (
  event: CommandObservation | IPythonObservation,
): string => {
  let { content } = event;
  if (content.length > MAX_CONTENT_LENGTH) {
    content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `Output:\n\`\`\`sh\n${content.trim() || "[Command finished execution with no output]"}\n\`\`\``;
};

const getEditObservationContent = (
  event: EditObservation,
  successMessage: boolean,
): string => {
  if (successMessage) {
    return `\`\`\`diff\n${event.extras.diff}\n\`\`\``; // Content is already truncated by the ACI
  }
  return event.content;
};

const getBrowseObservationContent = (event: BrowseObservation) => {
  let contentDetails = `**URL:** ${event.extras.url}\n`;
  if (event.extras.error) {
    contentDetails += `\n\n**Error:**\n${event.extras.error}\n`;
  }
  contentDetails += `\n\n**Output:**\n${event.content}`;
  if (contentDetails.length > MAX_CONTENT_LENGTH) {
    contentDetails = `${contentDetails.slice(0, MAX_CONTENT_LENGTH)}...(truncated)`;
  }
  return contentDetails;
};

const getMcpObservationContent = (event: OpenHandsObservation): string => {
  let { content } = event;
  if (content.length > MAX_CONTENT_LENGTH) {
    content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `**Output:**\n\`\`\`\n${content.trim() || "[MCP Tool finished execution with no output]"}\n\`\`\``;
};

export const getObservationContent = (event: OpenHandsObservation): string => {
  switch (event.observation) {
    case "read":
      return getReadObservationContent(event);
    case "edit":
      return getEditObservationContent(event, isSuccessObservation(event));
    case "run_ipython":
    case "run":
      return getCommandObservationContent(event);
    case "browse":
      return getBrowseObservationContent(event);
    case "mcp":
      return getMcpObservationContent(event);
    default:
      return getDefaultEventContent(event);
  }
};
