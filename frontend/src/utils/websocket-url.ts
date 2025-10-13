/**
 * Builds the WebSocket URL for V1 conversations
 * @param conversationId The conversation ID
 * @param conversationUrl The conversation URL containing host/port (e.g., "http://localhost:3000/api/conversations/123")
 * @param sessionApiKey The session API key for authentication
 * @returns WebSocket URL or null if inputs are invalid
 */
export function buildWebSocketUrl(
  conversationId: string | undefined,
  conversationUrl: string | null | undefined,
  sessionApiKey: string | null | undefined,
): string | null {
  if (!conversationId) {
    return null;
  }

  // Extract base URL and port from conversation.url
  let baseUrl = "";
  if (conversationUrl && !conversationUrl.startsWith("/")) {
    try {
      const url = new URL(conversationUrl);
      baseUrl = url.host; // e.g., "localhost:3000"
    } catch {
      baseUrl = window.location.host;
    }
  } else {
    baseUrl = window.location.host;
  }

  // Build WebSocket URL: ws://host:port/sockets/events/{conversationId}?session_api_key={key}
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const sessionKey = sessionApiKey ? `?session_api_key=${sessionApiKey}` : "";

  return `${protocol}//${baseUrl}/sockets/events/${conversationId}${sessionKey}`;
}
