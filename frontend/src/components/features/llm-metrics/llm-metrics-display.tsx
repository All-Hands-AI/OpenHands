import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";

export function LLMMetricsDisplay() {
  const { isVisible } = useSelector((state: RootState) => state.costVisibility);
  const metrics = useSelector((state: RootState) => state.llmMetrics);

  if (!isVisible || !metrics) {
    return null;
  }

  return (
    <div className="grid grid-cols-2 gap-1 p-2">
      <div className="flex flex-col">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Cost:</span>
          <span className="text-sm font-medium">
            ${metrics.accumulatedCost.toFixed(4)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Total Tokens:</span>
          <span className="text-sm font-medium">{metrics.totalTokens}</span>
        </div>
      </div>
      <div className="flex flex-col">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Prompt Tokens:</span>
          <span className="text-sm font-medium">{metrics.promptTokens}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Completion Tokens:</span>
          <span className="text-sm font-medium">{metrics.completionTokens}</span>
        </div>
      </div>
    </div>
  );
}
