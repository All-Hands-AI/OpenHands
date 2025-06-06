import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";

type LocalizedFormatter = (date: string | Date) => string;

export function useLocalizedDateFormatter(
  formatType?: "date" | "time",
): LocalizedFormatter {
  const { i18n } = useTranslation();

  const formatterOptions: Intl.DateTimeFormatOptions =
    formatType === "time"
      ? {
          hour: "2-digit",
          minute: "2-digit",
        }
      : {
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        };

  const formatter = useMemo(
    () => new Intl.DateTimeFormat(i18n.language, formatterOptions),
    [i18n.language],
  );

  const wrappedFormatter = useCallback(
    (value: string | Date) =>
      formatter.format(typeof value === "string" ? new Date(value) : value),
    [formatter],
  );

  return wrappedFormatter;
}
