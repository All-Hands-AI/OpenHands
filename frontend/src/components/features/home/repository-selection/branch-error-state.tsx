import React from "react";
import { useTranslation } from "react-i18next";

export function BranchErrorState() {
  const { t } = useTranslation();
  return (
    <div
      data-testid="branch-dropdown-error"
      className="flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded-sm text-red-500"
    >
      <span className="text-sm">{t("HOME$FAILED_TO_LOAD_BRANCHES")}</span>
    </div>
  );
}
