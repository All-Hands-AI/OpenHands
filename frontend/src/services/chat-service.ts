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

export function createUserFeedback(
  feedbackType: "positive" | "negative",
  targetType: "message" | "trajectory",
  targetId?: number,
) {
  const event = {
    action: ActionType.USER_FEEDBACK,
    args: {
      feedback_type: feedbackType,
      target_type: targetType,
      target_id: targetId,
    },
  };
  return event;
}
