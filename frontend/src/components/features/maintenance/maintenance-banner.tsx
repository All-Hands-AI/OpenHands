import React from "react";
import { useTranslation } from "react-i18next";

interface MaintenanceBannerProps {
  startTime: string;
}

export function MaintenanceBanner({ startTime }: MaintenanceBannerProps) {
  const { t } = useTranslation();
  // Convert EST timestamp to user's local timezone
  const formatMaintenanceTime = (estTimeString: string): string => {
    try {
      // Parse the EST timestamp
      // If the string doesn't include timezone info, assume it's EST
      let dateToFormat: Date;

      if (
        estTimeString.includes("T") &&
        (estTimeString.includes("-05:00") ||
          estTimeString.includes("-04:00") ||
          estTimeString.includes("EST") ||
          estTimeString.includes("EDT"))
      ) {
        // Already has timezone info
        dateToFormat = new Date(estTimeString);
      } else {
        // Assume EST and convert to UTC for proper parsing
        // EST is UTC-5, EDT is UTC-4, but we'll assume EST for simplicity
        const estDate = new Date(estTimeString);
        if (Number.isNaN(estDate.getTime())) {
          throw new Error("Invalid date");
        }
        dateToFormat = estDate;
      }

      // Format to user's local timezone
      return dateToFormat.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
      });
    } catch (error) {
      // Fallback to original string if parsing fails
      // eslint-disable-next-line no-console
      console.warn("Failed to parse maintenance time:", error);
      return estTimeString;
    }
  };

  const localTime = formatMaintenanceTime(startTime);

  return (
    <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-3">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-500"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium">
            {t("MAINTENANCE$SCHEDULED_MESSAGE", { time: localTime })}
          </p>
        </div>
      </div>
    </div>
  );
}
