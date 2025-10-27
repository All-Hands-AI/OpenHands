import { useLocation, useParams } from "react-router";

export function useConversationId() {
  const { conversationId } = useParams<{ conversationId: string }>();

  const location = useLocation();
  const isMicroagentManagementRoute =
    location.pathname === "/microagent-management";

  if (!conversationId && !isMicroagentManagementRoute) {
    throw new Error(
      "useConversationId must be used within a route that has a conversationId parameter",
    );
  }

  return { conversationId: conversationId || "" };
}
