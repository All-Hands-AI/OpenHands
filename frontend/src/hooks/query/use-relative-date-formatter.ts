import { useCallback } from "react";
import { useLocalizedDateFormatter } from "./use-localized-date-formatter";

type RelativeFormatter = (date: string | Date) => string;

export function useRelativeDateFormatter(): RelativeFormatter {
  const dateFormatter = useLocalizedDateFormatter("date");
  const timeFormatter = useLocalizedDateFormatter("time");

  const formatter = useCallback((value: string | Date) => {
    const now = new Date();
    const date = typeof value === "string" ? new Date(value) : value;
    const isToday =
      date.getFullYear() === now.getFullYear() &&
      date.getMonth() === now.getMonth() &&
      date.getDate() === now.getDate();
    return isToday ? timeFormatter(date) : dateFormatter(date);
  }, []);

  return formatter;
}
