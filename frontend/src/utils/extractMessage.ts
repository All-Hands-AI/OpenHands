const isMessage = (
  message: object,
): message is UserMessage | AssistantMessage =>
  "action" in message && message.action === "message";

const isIPythonAction = (message: object): message is IPythonAction =>
  "action" in message && message.action === "run_ipython";

const isCommandAction = (message: object): message is CommandAction =>
  "action" in message && message.action === "run";

const isFinishAction = (message: object): message is FinishAction =>
  "action" in message && message.action === "finish";

const isDelegateAction = (message: object): message is DelegateAction =>
  "action" in message && message.action === "delegate";

const isBrowseAction = (message: object): message is BrowseAction =>
  "action" in message && message.action === "browse";

const isBrowseInteractiveAction = (
  message: object,
): message is BrowseInteractiveAction =>
  "action" in message && message.action === "browse_interactive";

const isRejectAction = (message: object): message is RejectAction =>
  "action" in message && message.action === "reject";

const isDelegateObservation = (
  message: object,
): message is DelegateObservation =>
  "observation" in message && message.observation === "delegate";

export interface ParsedMessage {
  source: "assistant" | "user";
  content: string;
  imageUrls: string[];
}

export const extractMessage = (
  message: TrajectoryItem,
): ParsedMessage | null => {
  if (isMessage(message)) {
    return {
      source: message.source === "agent" ? "assistant" : "user",
      content: message.args.content,
      imageUrls: message.args.images_urls ?? [],
    };
  }

  if (
    isIPythonAction(message) ||
    isCommandAction(message) ||
    isBrowseInteractiveAction(message)
  ) {
    return {
      source: "assistant",
      content: message.args.thought || message.message,
      imageUrls: [],
    };
  }

  if (
    isFinishAction(message) ||
    isDelegateAction(message) ||
    isBrowseAction(message) ||
    isRejectAction(message)
  ) {
    return {
      source: "assistant",
      content: message.message,
      imageUrls: [],
    };
  }

  if (isDelegateObservation(message)) {
    return {
      source: "assistant",
      content: message.content,
      imageUrls: [],
    };
  }

  return null;
};
