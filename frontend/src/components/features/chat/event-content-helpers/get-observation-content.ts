import {
  ReadObservation,
  CommandObservation,
  IPythonObservation,
  EditObservation,
  BrowseObservation,
  OpenHandsObservation,
  RecallObservation,
} from "#/types/core/observations";
import { getObservationResult } from "./get-observation-result";
import { getDefaultEventContent, MAX_CONTENT_LENGTH } from "./shared";
import i18n from "#/i18n";

const getReadObservationContent = (event: ReadObservation): string =>
  `\`\`\`\n${event.content}\n\`\`\``;

const getCommandObservationContent = (
  event: CommandObservation | IPythonObservation,
): string => {
  let { content } = event;
  if (content.length > MAX_CONTENT_LENGTH) {
    content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
  }
  return `Output:\n\`\`\`sh\n${content.trim() || i18n.t("OBSERVATION$COMMAND_NO_OUTPUT")}\n\`\`\``;
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

const getRecallObservationContent = (event: RecallObservation): string => {
  let content = "";

  if (event.extras.recall_type === "workspace_context") {
    if (event.extras.repo_name) {
      content += `\n\n**Repository:** ${event.extras.repo_name}`;
    }
    if (event.extras.repo_directory) {
      content += `\n\n**Directory:** ${event.extras.repo_directory}`;
    }
    if (event.extras.date) {
      content += `\n\n**Date:** ${event.extras.date}`;
    }
    if (
      event.extras.runtime_hosts &&
      Object.keys(event.extras.runtime_hosts).length > 0
    ) {
      content += `\n\n**Available Hosts**`;
      for (const [host, port] of Object.entries(event.extras.runtime_hosts)) {
        content += `\n\n- ${host} (port ${port})`;
      }
    }
    if (event.extras.repo_instructions) {
      content += `\n\n**Repository Instructions:**\n\n${event.extras.repo_instructions}`;
    }
    if (event.extras.additional_agent_instructions) {
      content += `\n\n**Additional Instructions:**\n\n${event.extras.additional_agent_instructions}`;
    }
  }

  // Handle microagent knowledge
  if (
    event.extras.microagent_knowledge &&
    event.extras.microagent_knowledge.length > 0
  ) {
    content += `\n\n**Triggered Microagent Knowledge:**`;
    for (const knowledge of event.extras.microagent_knowledge) {
      content += `\n\n- **${knowledge.name}** (triggered by keyword: ${knowledge.trigger})\n\n\`\`\`\n${knowledge.content}\n\`\`\``;
    }
  }

  if (
    event.extras.custom_secrets_descriptions &&
    Object.keys(event.extras.custom_secrets_descriptions).length > 0
  ) {
    content += `\n\n**Custom Secrets**`;
    for (const [name, description] of Object.entries(
      event.extras.custom_secrets_descriptions,
    )) {
      content += `\n\n- $${name}: ${description}`;
    }
  }

  return content;
};

export const getObservationContent = (event: OpenHandsObservation): string => {
  switch (event.observation) {
    case "read":
      return getReadObservationContent(event);
    case "edit":
      return getEditObservationContent(
        event,
        getObservationResult(event) === "success",
      );
    case "run_ipython":
    case "run":
      return getCommandObservationContent(event);
    case "browse":
      return getBrowseObservationContent(event);
    case "recall":
      return getRecallObservationContent(event);
    default:
      return getDefaultEventContent(event);
  }
};
