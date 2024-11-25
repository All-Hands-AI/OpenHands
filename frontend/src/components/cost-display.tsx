import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";

export function CostDisplay() {
  const { totalCost, lastStepCosts } = useSelector((state: RootState) => state.cost);

  return (
    <div className="fixed bottom-24 right-4 bg-neutral-700 border border-neutral-600 rounded-lg p-3 text-sm">
      <div className="mb-2">
        <span className="text-neutral-400">Total Cost:</span>{" "}
        <span className="font-semibold">${totalCost.toFixed(4)}</span>
      </div>
      {lastStepCosts.length > 0 && (
        <div>
          <span className="text-neutral-400">Last Steps:</span>
          <div className="mt-1 space-y-1">
            {lastStepCosts.map((step, i) => (
              <div key={i} className="flex justify-between">
                <span className="text-neutral-300 truncate mr-4" title={step.description}>
                  {step.description}
                </span>
                <span className="text-neutral-300">${step.cost.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
