import React from "react";
import { useTranslation } from "react-i18next";
import { formatInTimeZone } from "date-fns-tz";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";

interface MaintenancePageProps {
  startTime: string;
  endTime: string;
}

export function MaintenancePage({ startTime, endTime }: MaintenancePageProps) {
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
    <div className="flex flex-col items-center justify-center min-h-screen bg-base p-4">
      <div className="bg-card rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        <div className="flex justify-center mb-6">
          <AllHandsLogo width={80} height={54} />
        </div>

        <h1 className="text-2xl font-bold mb-4">
          {t(I18nKey.MAINTENANCE$TITLE)}
        </h1>

        <p className="text-muted-foreground mb-6">
          {t(I18nKey.MAINTENANCE$DESCRIPTION)}
        </p>

        <div className="bg-muted p-4 rounded-md mb-6">
          <p className="font-medium mb-2">
            {t(I18nKey.MAINTENANCE$SCHEDULED_TIME)}
          </p>
          <p className="text-sm">
            <span className="font-medium">{t(I18nKey.MAINTENANCE$START)}:</span>{" "}
            {localStartTime}
          </p>
          <p className="text-sm">
            <span className="font-medium">{t(I18nKey.MAINTENANCE$END)}:</span>{" "}
            {localEndTime}
          </p>
        </div>

        <p className="text-sm text-muted-foreground">
          {t(I18nKey.MAINTENANCE$COME_BACK_LATER)}
        </p>
      </div>
    </div>
  );
}
