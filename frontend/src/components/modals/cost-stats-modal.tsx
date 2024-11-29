import React, { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";

export interface Cost {
  model: string;
  cost: number;
  timestamp: number;
}

export interface CostStats {
  accumulated_cost: number;
  costs: Cost[];
}

interface CostStatsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function CostStatsModal({ isOpen, onClose }: CostStatsModalProps): JSX.Element {
  const [costStats, setCostStats] = useState<CostStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetch("/api/costs")
        .then((response) => response.json())
        .then((data) => setCostStats(data))
        .catch((err) => setError(err.message));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const renderContent = () => {
    if (error) {
      return (
        <div className="text-red-500">Error loading cost data: {error}</div>
      );
    }

    if (!costStats) {
      return <div>Loading...</div>;
    }

    return (
      <div className="space-y-4">
        <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
          <div className="text-lg font-semibold">
            Total Cost: ${costStats.accumulated_cost.toFixed(4)}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-2">Recent Costs</h3>
          <div className="space-y-2">
            {costStats.costs.slice(-5).map((cost, index) => (
              <div
                key={index}
                className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded"
              >
                <div>
                  <span className="font-medium">{cost.model}</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                    ({formatDistanceToNow(cost.timestamp * 1000)} ago)
                  </span>
                </div>
                <div className="font-medium">${cost.cost.toFixed(4)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Cost Statistics</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>
        {renderContent()}
      </div>
    </div>
  );
}

export { CostStatsModal };
