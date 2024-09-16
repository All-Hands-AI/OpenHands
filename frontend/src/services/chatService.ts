import ActionType from "#/types/ActionType";

export function createChatMessage(
  message: string,
  images_urls: string[],
  timestamp: string,
) {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, images_urls, timestamp },
  };
  return JSON.stringify(event);
}
