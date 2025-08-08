import React from "react";
import { useConversationMicroagents } from "#/hooks/query/use-conversation-microagents";

interface MicroagentNamesOverlayProps {
  isVisible: boolean;
  onClose: () => void;
}

const TOGGLE_OVERLAY_HINT = "Press Ctrl + R to toggle • ESC to close";

export function MicroagentNamesOverlay({
  isVisible,
  onClose,
}: MicroagentNamesOverlayProps) {
  const { data: microagents, isLoading } = useConversationMicroagents();

  if (!isVisible) return null;

  // Filter for permanent microagents (repo type are always active)
  const permanentMicroagents =
    microagents?.filter((agent) => agent.type === "repo") || [];

  const NO_MICROAGENTS_TEXT = "No permanent microagents loaded";
  const PERMANENT_MICROAGENTS_HEADING = "Permanent Microagents";

  let content: React.ReactNode;
  if (isLoading) {
    content = (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
        <span className="ml-2 text-gray-600">Loading microagents...</span>
      </div>
    );
  } else if (permanentMicroagents.length > 0) {
    content = (
      <div className="space-y-2">
        {permanentMicroagents.map((agent, index) => (
          <div
            key={index}
            className="flex items-center p-3 bg-gray-50 rounded-lg"
          >
            <div className="w-2 h-2 bg-green-500 rounded-full mr-3" />
            <span className="font-medium text-gray-800">{agent.name}</span>
          </div>
        ))}
      </div>
    );
  } else {
    content = (
      <div className="text-center py-8 text-gray-500">
        {NO_MICROAGENTS_TEXT}
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">
            {PERMANENT_MICROAGENTS_HEADING}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-bold"
            type="button"
          >
            ×
          </button>
        </div>

        {content}

        <div className="mt-4 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            {TOGGLE_OVERLAY_HINT}
          </p>
        </div>
      </div>
    </div>
  );
}
