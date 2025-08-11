import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface LinearInstallButtonProps {
  "data-testid"?: string;
}

export function LinearInstallButton({
  "data-testid": dataTestId,
}: LinearInstallButtonProps) {
  const { t } = useTranslation();

  const handleInstallClick = () => {
    window.location.href = "https://app.all-hands-dev/integration/linear/workspaces";
  };

  return (
    <button
      onClick={handleInstallClick}
      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      data-testid={dataTestId}
    >
      {t(I18nKey.PROJECT_MANAGEMENT$INSTALL_LINEAR_APP)}
    </button>
  );
}