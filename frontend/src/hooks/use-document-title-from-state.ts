import { useEffect, useRef } from "react";
import { useParams } from "react-router";
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
    // If we have a valid title from the conversation data, update the document title
    if (conversation?.title) {
      lastValidTitleRef.current = conversation.title;
      document.title = `${conversation.title} - ${suffix}`;
    }
    // If the title is empty but we have a last valid title, keep using that
    else if (lastValidTitleRef.current) {
      document.title = `${lastValidTitleRef.current} - ${suffix}`;
    }
    // If no title is available at all, use the default
    else {
      document.title = suffix;
    }

    // Cleanup function to reset the title when the component unmounts
    return () => {
      document.title = suffix;
    };
  }, [conversation, suffix]);
}
