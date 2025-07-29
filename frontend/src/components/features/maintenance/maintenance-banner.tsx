import React from "react";
import { useTranslation } from "react-i18next";
import { formatInTimeZone } from "date-fns-tz";
import { I18nKey } from "#/i18n/declaration";

interface MaintenanceBannerProps {
  startTime: string;
  endTime: string;
}

export function MaintenanceBanner({
  startTime,
  endTime,
}: MaintenanceBannerProps) {
  const { t } = useTranslation();

  // Convert EST times to local timezone
  const formatTimeToLocal = (timeString: string) => {
    try {
      // Parse the time string - assuming it's in EST
      const date = new Date(timeString);

      // Get user's timezone
      const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      // First convert to EST timezone if the date doesn't already include timezone info
      // This ensures we're treating the input as EST time
      const estDate =
        !timeString.includes("Z") &&
        !timeString.includes("+") &&
        !timeString.includes("-")
          ? new Date(`${timeString} EST`)
          : date;

      // Format the date in user's local timezone
      const localTime = formatInTimeZone(
        estDate,
        userTimeZone,
        "MMM d, yyyy h:mm a",
      );

      // Get timezone abbreviation for user's timezone
      const timeZoneAbbr = formatInTimeZone(estDate, userTimeZone, "zzz");

      return `${localTime} ${timeZoneAbbr}`;
    } catch (error) {
      // Silently handle error and return original time string
      return timeString;
    }
  };

  const localStartTime = formatTimeToLocal(startTime);
  const localEndTime = formatTimeToLocal(endTime);

  return (
    <div className="bg-warning text-warning-foreground px-4 py-3 text-center text-sm font-medium">
      <div className="flex items-center justify-center gap-2">
        <svg
          className="h-4 w-4 flex-shrink-0"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
        <span>
          {t(I18nKey.MAINTENANCE$BANNER_MESSAGE)} {localStartTime} -{" "}
          {localEndTime}
        </span>
      </div>
    </div>
  );
}
