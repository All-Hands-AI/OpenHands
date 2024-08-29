const isMessage = (message: object): message is TrajectoryItem =>
  "action" in message && message.action === "message";

const isAssistantMessage = (message: object): message is AssistantMessage =>
  "source" in message && message.source === "agent";

const isUserMessage = (message: object): message is UserMessage =>
  // if message is received from ws, it contains source field
  ("source" in message && message.source === "user") ||
  !isAssistantMessage(message);

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

export interface SimplifiedMessage {
  source: "assistant" | "user";
  content: string;
  imageUrls: string[];
}

export const extractMessage = (
  message: TrajectoryItem,
): SimplifiedMessage | null => {
  if (isMessage(message)) {
    if (isAssistantMessage(message)) {
      return {
        source: "assistant",
        content: message.args.content,
        imageUrls: message.args.images_urls ?? [],
      };
    }

    if (isUserMessage(message)) {
      return {
        source: "user",
        content: message.args.content,
        imageUrls: message.args.images_urls,
      };
    }
  }

  if (isIPythonAction(message)) {
    return {
      source: "assistant",
      content: message.args.thought,
      imageUrls: [],
    };
  }

  if (isCommandAction(message)) {
    return {
      source: "assistant",
      content: message.args.thought,
      imageUrls: [],
    };
  }

  if (isFinishAction(message)) {
    return {
      source: "assistant",
      content: message.message,
      imageUrls: [],
    };
  }

  if (isDelegateAction(message)) {
    return {
      source: "assistant",
      content: message.message,
      imageUrls: [],
    };
  }

  if (isBrowseAction(message)) {
    return {
      source: "assistant",
      content: message.message,
      imageUrls: [],
    };
  }

  if (isBrowseInteractiveAction(message)) {
    return {
      source: "assistant",
      content: message.args.thought || message.message,
      imageUrls: [],
    };
  }

  if (isRejectAction(message)) {
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
