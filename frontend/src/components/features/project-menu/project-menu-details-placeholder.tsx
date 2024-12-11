import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";
import CloudConnection from "#/icons/cloud-connection.svg?react";
import { I18nKey } from "#/i18n/declaration";

interface ProjectMenuDetailsPlaceholderProps {
  isConnectedToGitHub: boolean;
  onConnectToGitHub: () => void;
}

export function ProjectMenuDetailsPlaceholder({
  isConnectedToGitHub,
  onConnectToGitHub,
}: ProjectMenuDetailsPlaceholderProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col">
      <span className="text-sm leading-6 font-semibold">
        {t(I18nKey.PROJECT_MENU_DETAILS_PLACEHOLDER$NEW_PROJECT_LABEL)}
      </span>
      <button
        type="button"
        onClick={onConnectToGitHub}
        disabled={isConnectedToGitHub}
      >
        <span
          className={cn(
            "text-xs leading-4 text-[#A3A3A3] flex items-center gap-2",
            "hover:underline hover:underline-offset-2",
          )}
        >
          {!isConnectedToGitHub
            ? t(I18nKey.PROJECT_MENU_DETAILS_PLACEHOLDER$CONNECT_TO_GITHUB)
            : t(I18nKey.PROJECT_MENU_DETAILS_PLACEHOLDER$CONNECTED)}
          <CloudConnection width={12} height={12} />
        </span>
      </button>
    </div>
  );
}
