import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useLinearInstall } from "#/hooks/mutation/use-linear-install";

interface LinearInstallButtonProps {
  "data-testid"?: string;
}

export function LinearInstallButton({
  "data-testid": dataTestId,
}: LinearInstallButtonProps) {
  const { t } = useTranslation();
  const linearInstallMutation = useLinearInstall();

  const handleInstallClick = () => {
    linearInstallMutation.mutate();
  };

  return (
    <button
      type="button"
      onClick={handleInstallClick}
      disabled={linearInstallMutation.isPending}
      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      data-testid={dataTestId}
    >
      {linearInstallMutation.isPending
        ? "Installing..."
        : t(I18nKey.PROJECT_MANAGEMENT$INSTALL_LINEAR_APP)}
    </button>
  );
}
