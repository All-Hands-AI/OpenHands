import { useEffect, useRef } from "react";

/**
 * A simplified version of the useDocumentTitle hook for testing
 * This version doesn't depend on Redux
 */
export function useDocumentTitleForTest(
  title?: string | null,
  suffix = "OpenHands",
) {
  // Keep track of the last valid title to prevent flickering
  const lastValidTitleRef = useRef<string | null>(null);

  // Use the provided title
  const effectiveTitle = title;

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
