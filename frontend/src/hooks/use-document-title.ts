import { useEffect } from "react";

/**
 * Hook to update the document title
 * @param title The title to set for the document
 * @param suffix Optional suffix to append to the title (defaults to "OpenHands")
 */
export function useDocumentTitle(
  title: string | null | undefined,
  suffix = "OpenHands",
) {
  useEffect(() => {
    const previousTitle = document.title;

    if (title) {
      document.title = `${title} | ${suffix}`;
    } else {
      document.title = suffix;
    }

    // Restore the previous title when the component unmounts
    return () => {
      document.title = previousTitle;
    };
  }, [title, suffix]);
}
