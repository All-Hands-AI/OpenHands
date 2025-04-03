import { useEffect } from "react";

/**
 * Hook to update the document title
 * @param title The title to set for the document
 * @param prefix Optional prefix to prepend to the title (defaults to "OpenHands")
 */
export function useDocumentTitle(
  title: string | null | undefined,
  prefix = "OpenHands",
) {
  useEffect(() => {
    const previousTitle = document.title;

    if (title) {
      document.title = `${prefix} | ${title}`;
    } else {
      document.title = prefix;
    }

    // Restore the previous title when the component unmounts
    return () => {
      document.title = previousTitle;
    };
  }, [title, prefix]);
}
