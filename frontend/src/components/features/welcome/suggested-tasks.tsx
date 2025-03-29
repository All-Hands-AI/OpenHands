import React, { useEffect, useState } from "react";
import { retrieveGitHubSuggestedTasks, SuggestedTask } from "#/api/github";
import { useGitHubUser } from "#/hooks/query/use-github-user";

// Helper function to get task icon based on task type
const getTaskIcon = (taskType: SuggestedTask["task_type"]) => {
  switch (taskType) {
    case "MERGE_CONFLICTS":
      return "⚠️"; // Merge conflicts
    case "FAILING_CHECKS":
      return "✖️"; // Failing checks
    case "UNRESOLVED_COMMENTS":
      return "💬"; // Unresolved comments
    case "OPEN_ISSUE":
      return "🐛"; // Open issue
    case "OPEN_PR":
      return "⤴️"; // Open PR
    default:
      return "📋"; // Default
  }
};

// Helper function to get task description based on task type
const getTaskDescription = (taskType: SuggestedTask["task_type"]) => {
  switch (taskType) {
    case "MERGE_CONFLICTS":
      return "Resolve merge conflicts";
    case "FAILING_CHECKS":
      return "Fix failing checks";
    case "UNRESOLVED_COMMENTS":
      return "Address review comments";
    case "OPEN_ISSUE":
      return "Work on issue";
    case "OPEN_PR":
      return "Review PR";
    default:
      return "Task";
  }
};

export function SuggestedTasks() {
  const [tasks, setTasks] = useState<SuggestedTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: user } = useGitHubUser();

  useEffect(() => {
    const fetchTasks = async () => {
      if (!user) return;

      setLoading(true);
      setError(null);

      try {
        const suggestedTasks = await retrieveGitHubSuggestedTasks();
        setTasks(suggestedTasks);
      } catch (err) {
        // Silently handle error and show user-friendly message
        setError("Failed to load suggested tasks");
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [user]);

  const handleTaskClick = (task: SuggestedTask) => {
    // Open the task in a new tab
    window.open(
      `https://github.com/${task.repo}/issues/${task.issue_number}`,
      "_blank",
    );
  };

  return (
    <div className="w-full">
      <h2 className="text-xl font-semibold mb-4">Suggested Tasks</h2>

      {loading && (
        <div className="flex justify-center items-center min-h-[100px]">
          <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-white" />
        </div>
      )}

      {error && (
        <div className="text-red-500 min-h-[100px] flex items-center justify-center">
          {error}
        </div>
      )}

      {!loading && !error && tasks.length === 0 && user && (
        <div className="text-gray-400 min-h-[100px] flex items-center justify-center">
          No suggested tasks found
        </div>
      )}

      {!loading && !error && !user && (
        <div className="text-gray-400 min-h-[100px] flex items-center justify-center">
          Sign in with GitHub to see suggested tasks
        </div>
      )}

      {!loading && !error && tasks.length > 0 && (
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
          {tasks.map((task, index) => (
            <div
              key={`${task.repo}-${task.issue_number}-${index}`}
              className="bg-[#2A2A2A] p-3 rounded-md border border-[#525252] hover:bg-[#333333] cursor-pointer transition-colors"
              onClick={() => handleTaskClick(task)}
            >
              <div className="flex items-start">
                <div className="mr-3 text-xl">
                  {getTaskIcon(task.task_type)}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium">{task.title}</div>
                  <div className="text-xs text-gray-400 mt-1 flex justify-between">
                    <span>{task.repo}</span>
                    <span>{getTaskDescription(task.task_type)}</span>
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
