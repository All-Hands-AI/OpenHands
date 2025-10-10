import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useAgentStore } from "#/stores/agent-store";
import { AgentState } from "#/types/agent-state";
import { useStreamStartAppConversation } from "#/hooks/mutation/use-stream-start-app-conversation";
import {
  AppConversationStartRequest,
  AppConversationStartTask,
} from "#/api/open-hands.types";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

// Component that shows in the chat input area during setup
function ConversationSetupInput({
  task,
}: {
  task: AppConversationStartTask | null;
}) {
  if (!task) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner />
        <span className="ml-2">Initializing conversation...</span>
      </div>
    );
  }

  const getStatusMessage = (status: string) => {
    const messages = {
      WORKING: "Starting your conversation...",
      WAITING_FOR_SANDBOX: "Setting up secure environment...",
      PREPARING_REPOSITORY: "Preparing repository...",
      RUNNING_SETUP_SCRIPT: "Running setup scripts...",
      SETTING_UP_GIT_HOOKS: "Configuring git integration...",
      STARTING_CONVERSATION: "Almost ready...",
      READY: "Conversation ready!",
      ERROR: "Setup failed",
    };
    return messages[status] || status;
  };

  const getProgress = (status: string) => {
    const progress = {
      WORKING: 10,
      WAITING_FOR_SANDBOX: 25,
      PREPARING_REPOSITORY: 50,
      RUNNING_SETUP_SCRIPT: 70,
      SETTING_UP_GIT_HOOKS: 85,
      STARTING_CONVERSATION: 95,
      READY: 100,
      ERROR: 0,
    };
    return progress[status] || 0;
  };

  return (
    <div className="space-y-3">
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${getProgress(task.status)}%` }}
        />
      </div>

      {/* Status message */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {getStatusMessage(task.status)}
        </span>
        {task.status !== "ERROR" && task.status !== "READY" && (
          <LoadingSpinner size="small" />
        )}
      </div>

      {/* Detail message */}
      {task.detail && <p className="text-xs text-gray-500">{task.detail}</p>}

      {/* Error state */}
      {task.status === "ERROR" && (
        <div className="flex items-center justify-between">
          <span className="text-red-600 text-sm">
            Setup failed. Please try again.
          </span>
          <button
            type="button"
            onClick={() => {
              window.location.href = "/";
            }}
            className="text-blue-500 hover:underline text-sm"
          >
            Return to Home
          </button>
        </div>
      )}
    </div>
  );
}

// Component that shows setup steps in the main chat area
function ConversationSetupProgress({
  task,
  error,
}: {
  task: AppConversationStartTask | null;
  error: Error | null;
}) {
  const setupSteps = [
    { key: "WORKING", label: "Initializing", completed: false },
    {
      key: "WAITING_FOR_SANDBOX",
      label: "Setting up environment",
      completed: false,
    },
    {
      key: "PREPARING_REPOSITORY",
      label: "Preparing repository",
      completed: false,
    },
    { key: "RUNNING_SETUP_SCRIPT", label: "Running setup", completed: false },
    { key: "SETTING_UP_GIT_HOOKS", label: "Configuring git", completed: false },
    {
      key: "STARTING_CONVERSATION",
      label: "Starting conversation",
      completed: false,
    },
  ];

  // Mark steps as completed based on current status
  const currentStepIndex = setupSteps.findIndex(
    (step) => step.key === task?.status,
  );
  const stepsWithStatus = setupSteps.map((step, index) => ({
    ...step,
    completed: index < currentStepIndex,
    current: index === currentStepIndex,
  }));

  return (
    <div className="max-w-md space-y-4">
      <h3 className="text-lg font-semibold text-center">
        Setting up your conversation
      </h3>

      <div className="space-y-2">
        {stepsWithStatus.map((step, index) => (
          <div key={step.key} className="flex items-center space-x-3">
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                step.completed
                  ? "bg-green-500 text-white"
                  : step.current
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-500"
              }`}
            >
              {step.completed ? "✓" : index + 1}
            </div>
            <span
              className={
                step.current
                  ? "font-medium text-blue-600"
                  : step.completed
                    ? "text-green-600"
                    : "text-gray-500"
              }
            >
              {step.label}
            </span>
            {step.current && <LoadingSpinner size="small" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="text-red-600 text-sm text-center">{error.message}</div>
      )}
    </div>
  );
}

interface ConversationSetupFlowProps {
  conversationId: string;
}

export function ConversationSetupFlow({
  conversationId,
}: ConversationSetupFlowProps) {
  const navigate = useNavigate();
  const [currentTask, setCurrentTask] =
    useState<AppConversationStartTask | null>(null);
  const { setCurrentAgentState } = useAgentStore();

  const { mutate: startConversation, error } = useStreamStartAppConversation();

  useEffect(() => {
    // Set agent state to loading during setup
    setCurrentAgentState(AgentState.LOADING);

    // Start the V1 conversation creation
    const request: AppConversationStartRequest = {
      // Get from user settings, context, etc.
      initial_message: {
        message: "Hello! I'm ready to help you with your project.",
        image_urls: [],
      },
    };

    startConversation({
      request,
      onProgress: (task) => {
        setCurrentTask(task);

        // When ready, replace URL and let existing logic take over
        if (task.status === "READY" && task.app_conversation_id) {
          // Replace the URL without the setup parameter
          navigate(`/conversations/${task.app_conversation_id}`, {
            replace: true,
          });
          // The existing conversation logic will now load the real conversation
        }
      },
    });
  }, [conversationId, startConversation, setCurrentAgentState, navigate]);

  return (
    <div className="flex flex-col h-full">
      {/* Empty messages area - could show setup steps here */}
      <div className="flex-1 flex items-center justify-center">
        <ConversationSetupProgress task={currentTask} error={error} />
      </div>

      {/* Setup progress in place of chat input */}
      <div className="border-t bg-white p-4">
        <ConversationSetupInput task={currentTask} />
      </div>
    </div>
  );
}
