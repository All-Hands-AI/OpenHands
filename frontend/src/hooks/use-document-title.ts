import { useEffect } from "react";

/**
 * Hook to update the document title
 * 
 * @param title The title to set for the document
 * @param suffix Optional suffix to append to the title (default: "OpenHands")
 */
export function useDocumentTitle(title: string | undefined | null, suffix = "OpenHands") {
  useEffect(() => {
    // If title is empty or not provided, use the default title
    if (!title) {
      document.title = suffix;
      return;
    }

    // Set the document title with the conversation title and suffix
    document.title = `${title} - ${suffix}`;

    // Cleanup function to reset the title when the component unmounts
    return () => {
      document.title = suffix;
    };
  }, [title, suffix]);
}