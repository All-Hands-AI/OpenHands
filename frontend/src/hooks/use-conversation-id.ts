import { useParams } from "react-router";

export function useConversationId() {
  const { conversationId } = useParams<{ conversationId: string }>();

  if (!conversationId) {
    throw new Error(
      "useConversationId must be used within a route that has a conversationId parameter",
    );
  }

  return { conversationId };
}
