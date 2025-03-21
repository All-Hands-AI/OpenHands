import { useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";

/**
 * Hook that updates the document title based on the conversation title in the Redux state.
 * This ensures that any changes to the conversation title are reflected in the document title.
 *
 * @param suffix Optional suffix to append to the title (default: "OpenHands")
 */
export function useDocumentTitleFromState(suffix = "OpenHands") {
  const conversationTitle = useSelector(
    (state: RootState) => state.conversation.title,
  );
  const lastValidTitleRef = useRef<string | null>(null);

  useEffect(() => {
    // If we have a valid title in the state, update the document title
    if (conversationTitle) {
      lastValidTitleRef.current = conversationTitle;
      document.title = `${conversationTitle} - ${suffix}`;
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
  }, [conversationTitle, suffix]);
}
