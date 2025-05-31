import React from "react";
import { useTranslation } from "react-i18next";
import { useSettings } from "#/hooks/query/use-settings";

function UserSettingsScreen() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useSettings();

  return (
    <div data-testid="user-settings-screen" className="flex flex-col h-full">
      <div className="p-9 flex flex-col gap-6">
        <h2 className="text-lg font-medium">{t("SETTINGS$USER_TITLE")}</h2>

        {isLoading ? (
          <div className="animate-pulse h-8 w-64 bg-tertiary rounded" />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm text-secondary">
                {t("SETTINGS$USER_EMAIL")}
              </label>
              <div className="text-base text-primary p-2 bg-base-tertiary rounded border border-tertiary">
                {settings?.EMAIL || t("SETTINGS$USER_EMAIL_NOT_AVAILABLE")}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserSettingsScreen;
