import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface BudgetUsageTextProps {
  currentCost: number;
  maxBudget: number;
}

export function BudgetUsageText({
  currentCost,
  maxBudget,
}: BudgetUsageTextProps) {
  const { t } = useTranslation();
  const usagePercentage = (currentCost / maxBudget) * 100;

  return (
    <div className="flex justify-end">
      <span className="text-xs text-neutral-400">
        ${currentCost.toFixed(4)} / ${maxBudget.toFixed(4)} (
        {usagePercentage.toFixed(2)}% {t(I18nKey.CONVERSATION$USED)})
      </span>
    </div>
  );
}
