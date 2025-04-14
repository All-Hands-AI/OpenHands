import { ReactNode } from "react";
import EventLogger from "#/utils/event-logger";

/**
 * Decodes HTML entities in a string
 * @param text The text to decode
 * @returns The decoded text
 */
const decodeHtmlEntities = (text: string): string => {
  const textarea = document.createElement("textarea");
  textarea.innerHTML = text;
  return textarea.value;
};

/**
 * Extracts the filename from a path
 * @param path The full path
 * @returns The filename (last part of the path)
 */
const extractFilename = (path: string): string => {
  if (!path) return "";
  // Handle both Unix and Windows paths
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1];
};

/**
 * Component that displays only the filename in the text but shows the full path on hover
 * Similar to MonoComponent but with path-specific functionality
 */
function PathComponent(props: { children?: ReactNode }) {
  const { children } = props;

  const processPath = (path: string) => {
    try {
      // First decode any HTML entities in the path
      const decodedPath = decodeHtmlEntities(path);
      // Extract the filename from the decoded path
      const filename = extractFilename(decodedPath);
      return (
        <span className="font-mono" title={decodedPath}>
          {filename}
        </span>
      );
    } catch (e) {
      // Just log the error without any message to avoid localization issues
      EventLogger.error(String(e));
      return <span className="font-mono">{path}</span>;
    }
  };

  if (Array.isArray(children)) {
    const processedChildren = children.map((child) =>
      typeof child === "string" ? processPath(child) : child,
    );

    return <strong className="font-mono">{processedChildren}</strong>;
  }

  if (typeof children === "string") {
    return <strong>{processPath(children)}</strong>;
  }

  return <strong className="font-mono">{children}</strong>;
}

export { PathComponent };
