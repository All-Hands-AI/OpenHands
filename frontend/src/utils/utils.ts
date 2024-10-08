import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface EventActionHistory {
  args?: {
    LLM_API_KEY?: string;
    [key: string]: unknown;
  };
  extras?: {
    open_page_urls: string[];
    active_page_index: number;
    dom_object: Record<string, unknown>;
    axtree_object: Record<string, unknown>;
    extra_element_properties: Record<string, unknown>;
    last_browser_action: string;
    last_browser_action_error: unknown;
    focused_element_bid: string;
  };
  [key: string]: unknown;
}

export const removeUnwantedKeys = (
  data: EventActionHistory[],
): EventActionHistory[] => {
  const UNDESIRED_KEYS = [
    "open_page_urls",
    "active_page_index",
    "dom_object",
    "axtree_object",
    "extra_element_properties",
    "last_browser_action",
    "last_browser_action_error",
    "focused_element_bid",
  ];

  return data.map((item) => {
    // Create a shallow copy of item
    const newItem = { ...item };

    // Check if extras exists and delete it from a new extras object
    if (newItem.extras) {
      const newExtras = { ...newItem.extras };
      UNDESIRED_KEYS.forEach((key) => {
        delete newExtras[key as keyof typeof newExtras];
      });
      newItem.extras = newExtras;
    }

    return newItem;
  });
};

export const removeApiKey = (
  data: EventActionHistory[],
): EventActionHistory[] =>
  data.map((item) => {
    // Create a shallow copy of item
    const newItem = { ...item };

    // Check if LLM_API_KEY exists and delete it from a new args object
    if (newItem.args?.LLM_API_KEY) {
      const newArgs = { ...newItem.args };
      delete newArgs.LLM_API_KEY;
      newItem.args = newArgs;
    }

    return newItem;
  });

export const getExtension = (code: string) => {
  if (code.includes(".")) return code.split(".").pop() || "";
  return "";
};

/**
 * Format a timestamp to a human-readable format
 * @param timestamp The timestamp to format (ISO 8601)
 * @returns The formatted timestamp
 *
 * @example
 * formatTimestamp("2021-10-10T10:10:10.000") // "10/10/2021, 10:10:10"
 * formatTimestamp("2021-10-10T22:10:10.000") // "10/10/2021, 22:10:10"
 */
export const formatTimestamp = (timestamp: string) =>
  new Date(timestamp).toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
