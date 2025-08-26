import React from "react";
import { useTranslation } from "react-i18next";

interface ErrorMessageProps {
  isError: boolean;
}

export function ErrorMessage({ isError }: ErrorMessageProps) {
  const { t } = useTranslation();
  
  if (!isError) return null;
  
  return (
    <div
      className="text-red-500 text-sm mt-1"
      data-testid="git-repo-dropdown-error"
    >
      {t("HOME$FAILED_TO_LOAD_REPOSITORIES")}
    </div>
  );
}