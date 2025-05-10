import { useState } from "react";

interface ProgressModalHook {
  isOpen: boolean;
  conversationId: string | null;
  openProgressModal: (conversationId: string) => void;
  closeProgressModal: () => void;
}

export const useProgressModal = (): ProgressModalHook => {
  const [isOpen, setIsOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const openProgressModal = (id: string) => {
    setConversationId(id);
    setIsOpen(true);
  };

  const closeProgressModal = () => {
    setIsOpen(false);
  };

  return {
    isOpen,
    conversationId,
    openProgressModal,
    closeProgressModal,
  };
};
