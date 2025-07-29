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
    <div className="bg-primary text-[#0D0F11] p-4 mb-3">
      <div className="flex items-center">
        <div className="ml-3">
          <p className="text-sm font-medium">
            {t("MAINTENANCE$SCHEDULED_MESSAGE", { time: localTime })}
          </p>
        </div>
      </div>
    </div>
  );
}
