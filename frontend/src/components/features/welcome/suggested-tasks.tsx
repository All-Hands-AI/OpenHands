import React from "react";
import { useNavigate } from "react-router";
import { useGitHubSuggestedTasks } from "#/hooks/query/use-github-suggested-tasks";
import { TaskType } from "#/api/github";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useConfig } from "#/hooks/query/use-config";

// Helper function to get a human-readable task type
const getTaskTypeLabel = (taskType: TaskType): string => {
  switch (taskType) {
    case TaskType.MERGE_CONFLICTS:
      return "Resolve merge conflicts";
    case TaskType.FAILING_CHECKS:
      return "Fix failing checks";
    case TaskType.UNRESOLVED_COMMENTS:
      return "Address comments";
    case TaskType.OPEN_ISSUE:
      return "Work on issue";
    case TaskType.OPEN_PR:
      return "Review PR";
    default:
      return "Unknown task";
  }
};

export function SuggestedTasks() {
  const navigate = useNavigate();
  const { data: tasks, isLoading, error } = useGitHubSuggestedTasks();
  const { data: user } = useGitHubUser();
  const { data: config } = useConfig();

  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config?.APP_MODE || null,
    gitHubClientId: config?.GITHUB_CLIENT_ID || null,
  });

  const handleTaskClick = () => {
    // This would typically navigate to the workspace with the task context
    // For now, we'll just navigate to the workspace
    navigate("/workspace");
  };

  return (
    <div className="w-full">
      <h2 className="text-xl font-semibold mb-4">Suggested Tasks</h2>

      {!user && (
        <div className="bg-[#2A2A2A] rounded-md p-4 border border-[#525252]">
          <p className="text-sm text-gray-300 mb-3">
            Connect to GitHub to see suggested tasks from your repositories.
          </p>
          <a
            href={gitHubAuthUrl || "#"}
            className="text-white bg-[#333333] hover:bg-[#444444] px-3 py-1 rounded-md text-sm inline-block"
            data-testid="connect-to-github"
          >
            Connect to GitHub
          </a>
        </div>
      )}

      {isLoading && user && (
        <div className="flex items-center justify-center min-h-[100px]">
          <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-white" />
        </div>
      )}

      {error && (
        <div className="bg-[#3A2A2A] rounded-md p-4 border border-[#725252] text-[#F5A9A9]">
          <p className="text-sm">
            Failed to load suggested tasks. Please try again later.
          </p>
        </div>
      )}

      {tasks && tasks.length === 0 && user && (
        <div className="bg-[#2A2A2A] rounded-md p-4 border border-[#525252]">
          <p className="text-sm text-gray-300">No suggested tasks found.</p>
        </div>
      )}

      {tasks && tasks.length > 0 && (
        <div className="space-y-2">
          {tasks.map((task, index) => (
            <div
              key={`${task.repo}-${task.issue_number}-${index}`}
              className="bg-[#2A2A2A] rounded-md p-3 border border-[#525252] hover:bg-[#333333] cursor-pointer transition-colors"
              onClick={handleTaskClick}
            >
              <div className="flex items-start">
                <div className="flex-1">
                  <div className="text-sm font-medium mb-1">{task.title}</div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">{task.repo}</span>
                    <span className="text-xs px-2 py-0.5 bg-[#3A3A3A] rounded-full">
                      {getTaskTypeLabel(task.task_type)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
