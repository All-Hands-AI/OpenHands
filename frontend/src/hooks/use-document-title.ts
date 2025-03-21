import { useEffect, useRef } from "react";

/**
 * Hook to update the document title with persistence to prevent flickering
 * 
 * @param title The title to set for the document
 * @param suffix Optional suffix to append to the title (default: "OpenHands")
 */
export function useDocumentTitle(title: string | undefined | null, suffix = "OpenHands") {
  // Keep track of the last valid title to prevent flickering
  const lastValidTitleRef = useRef<string | null>(null);
  
  useEffect(() => {
    // If we have a valid title, update our ref and the document title
    if (title) {
      lastValidTitleRef.current = title;
      document.title = `${title} - ${suffix}`;
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
  }, [title, suffix]);
}