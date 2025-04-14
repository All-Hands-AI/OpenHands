import { useParams } from "react-router";
import { useEffect, useRef } from "react";
import { useUserConversation } from "./query/use-user-conversation";

/**
 * Hook that updates the document title based on the current conversation.
 * This ensures that any changes to the conversation title are reflected in the document title.
 *
 * @param suffix Optional suffix to append to the title (default: "OpenHands")
 */
export function useDocumentTitleFromState(suffix = "OpenHands") {
  const params = useParams();
  const { data: conversation } = useUserConversation(
    params.conversationId ?? null,
  );
  const lastValidTitleRef = useRef<string | null>(null);

  useEffect(() => {
    if (conversation?.title) {
      lastValidTitleRef.current = conversation.title;
      document.title = `${conversation.title} | ${suffix}`;
    } else {
      document.title = suffix;
    }

    return () => {
      document.title = suffix;
    };
  }, [conversation, suffix]);
}
