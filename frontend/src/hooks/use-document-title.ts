import { useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";

/**
 * Hook to update the document title with persistence to prevent flickering
 *
 * @param title The title to set for the document (optional, will use state if not provided)
 * @param suffix Optional suffix to append to the title (default: "OpenHands")
 */
export function useDocumentTitle(title?: string | null, suffix = "OpenHands") {
  // Keep track of the last valid title to prevent flickering
  const lastValidTitleRef = useRef<string | null>(null);

  // Get the conversation title from the state if available
  const conversationTitle = useSelector(
    (state: RootState) => state.conversation.title,
  );

  // Use the provided title or fall back to the conversation title from state
  const effectiveTitle = title !== undefined ? title : conversationTitle;

  useEffect(() => {
    // If we have a valid title, update our ref and the document title
    if (effectiveTitle) {
      lastValidTitleRef.current = effectiveTitle;
      document.title = `${effectiveTitle} - ${suffix}`;
    }
    // If title is empty but we have a last valid title, keep using that
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
  }, [effectiveTitle, suffix]);
}
