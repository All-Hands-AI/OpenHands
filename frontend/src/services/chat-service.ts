import ActionType from "#/types/action-type";

export function createChatMessage(
  message: string,
  image_urls: string[],
  timestamp: string,
) {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, image_urls, timestamp },
  };
  return event;
}
