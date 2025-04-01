import React from "react";
import toast from "react-hot-toast";
import { useWsClient } from "#/context/ws-client-provider";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { AgentState } from "#/types/agent-state";

interface CostThresholdToastProps {
  message: string;
}

// Define the component first before using it
function CostThresholdToast({
  message,
}: CostThresholdToastProps): React.ReactElement {
  const { send } = useWsClient();

  const handleApprove = (): void => {
    // Change agent state to RUNNING
    send(generateAgentStateChangeEvent(AgentState.RUNNING));
    toast.dismiss("cost-threshold-toast");
  };

  const handleReject = (): void => {
    // Keep agent in PAUSED state
    toast.dismiss("cost-threshold-toast");
  };

  return (
    <div className="max-w-md w-full bg-gray-800 shadow-lg rounded-lg pointer-events-auto flex flex-col ring-1 ring-black ring-opacity-5">
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0 pt-0.5">
            <svg
              className="h-6 w-6 text-yellow-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-white">
              Cost Threshold Alert
            </p>
            <p className="mt-1 text-sm text-gray-300">{message}</p>
          </div>
        </div>
      </div>
      <div className="flex border-t border-gray-700">
        <button
          type="button"
          onClick={handleApprove}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-bl-lg transition-colors"
        >
          Approve & Continue
        </button>
        <button
          type="button"
          onClick={handleReject}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-br-lg transition-colors border-l border-gray-700"
        >
          Reject
        </button>
      </div>
    </div>
  );
}

export const showCostThresholdToast = (message: string): void => {
  // Dismiss any existing cost threshold toasts
  toast.dismiss("cost-threshold-toast");

  // Show the custom toast
  toast.custom(() => <CostThresholdToast message={message} />, {
    id: "cost-threshold-toast",
    duration: Infinity, // Toast stays until user interacts with it
    position: "top-center",
  });
};
