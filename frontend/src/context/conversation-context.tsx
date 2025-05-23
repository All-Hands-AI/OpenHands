import { useConversationId } from "#/hooks/use-conversation-id";

// This file is kept for backward compatibility
// It re-exports the useConversationId hook as useConversation
export function useConversation() {
  return useConversationId();
}

// ConversationProvider is kept as a no-op component for backward compatibility
export function ConversationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
