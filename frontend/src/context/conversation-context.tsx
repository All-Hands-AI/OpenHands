import React from "react";

interface ConversationContextType {
  conversationId: string | null;
  setConversationId: (id: string | null) => void;
}

const ConversationContext = React.createContext<ConversationContextType>({
  conversationId: null,
  setConversationId: () => {},
});

export function ConversationProvider({ children }: { children: React.ReactNode }) {
  const [conversationId, setConversationId] = React.useState<string | null>(null);

  return (
    <ConversationContext.Provider value={{ conversationId, setConversationId }}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversation() {
  const context = React.useContext(ConversationContext);
  if (!context) {
    throw new Error("useConversation must be used within a ConversationProvider");
  }
  return context;
}