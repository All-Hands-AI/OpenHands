import React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";

export function RepositoryLoadingState() {
  const { t } = useTranslation();
  return (
    <div
      data-testid="repo-dropdown-loading"
      className="flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded"
    >
      <Spinner size="sm" />
      <span className="text-sm">{t("HOME$LOADING_REPOSITORIES")}</span>
    </div>
  );
}
