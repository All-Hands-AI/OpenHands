import React from "react";
import { WsClientProvider } from "#/context/ws-client-provider";
import { ConversationWebSocketProvider } from "#/contexts/conversation-websocket-context";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

interface WebSocketProviderWrapperProps {
  children: React.ReactNode;
  conversationId: string;
  version: 0 | 1;
}

/**
 * A wrapper component that conditionally renders either the old v0 WebSocket provider
 * or the new v1 WebSocket provider based on the version prop.
 *
 * @param version - 0 for old WsClientProvider, 1 for new ConversationWebSocketProvider
 * @param conversationId - The conversation ID to pass to the provider
 * @param children - The child components to wrap
 *
 * @example
 * // Use the old v0 provider
 * <WebSocketProviderWrapper version={0} conversationId="conv-123">
 *   <ChatComponent />
 * </WebSocketProviderWrapper>
 *
 * @example
 * // Use the new v1 provider
 * <WebSocketProviderWrapper version={1} conversationId="conv-123">
 *   <ChatComponent />
 * </WebSocketProviderWrapper>
 */
export function WebSocketProviderWrapper({
  children,
  conversationId,
  version,
}: WebSocketProviderWrapperProps) {
  // Get conversation data for V1 provider
  const { data: conversation } = useActiveConversation();

  if (version === 0) {
    return (
      <WsClientProvider conversationId={conversationId}>
        {children}
      </WsClientProvider>
    );
  }

  if (version === 1) {
    return (
      <ConversationWebSocketProvider
        conversationId={conversationId}
        conversationUrl={conversation?.url}
        sessionApiKey={conversation?.session_api_key}
      >
        {children}
      </ConversationWebSocketProvider>
    );
  }

  throw new Error(
    `Unsupported WebSocket provider version: ${version}. Supported versions are 0 and 1.`,
  );
}
