import React from "react";

interface BudgetProgressBarProps {
  currentCost: number;
  maxBudget: number;
}

export function BudgetProgressBar({
  currentCost,
  maxBudget,
}: BudgetProgressBarProps) {
  const usagePercentage = (currentCost / maxBudget) * 100;
  const isNearLimit = usagePercentage > 80;

  return (
    <div className="w-full h-1.5 bg-neutral-700 rounded-full overflow-hidden mt-1">
      <div
        className={`h-full transition-all duration-300 ${
          isNearLimit ? "bg-red-500" : "bg-blue-500"
        }`}
        style={{
          width: `${Math.min(100, usagePercentage)}%`,
        }}
      />
    </div>
  );
}
