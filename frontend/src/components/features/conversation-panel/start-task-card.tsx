import React from "react";
import { V1AppConversationStartTask } from "#/api/conversation-service/v1-conversation-service.api";
import { cn } from "#/utils/utils";

interface StartTaskCardProps {
  task: V1AppConversationStartTask;
}

export function StartTaskCard({ task }: StartTaskCardProps) {
  // Format status for display
  const formatStatus = (status: string) =>
    status
      .toLowerCase()
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

  // Get status color
  const getStatusColor = (status: string) => {
    if (status === "ERROR") return "text-danger";
    if (status === "READY") return "text-success";
    return "text-warning";
  };

  const title = task.request.title || task.detail || "Starting conversation...";

  return (
    <div
      data-testid="start-task-card"
      className={cn(
        "relative h-auto w-full p-3.5 border-b border-neutral-600 cursor-pointer",
        "hover:bg-[#454545]",
      )}
    >
      <div className="flex items-center justify-between w-full">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-neutral-100 truncate">
              {title}
            </h3>
            <span
              className={cn(
                "text-xs font-medium px-2 py-0.5 rounded",
                getStatusColor(task.status),
              )}
            >
              {formatStatus(task.status)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-2 flex flex-col gap-1 text-xs text-neutral-400">
        {task.request.selected_repository && (
          <div className="flex items-center gap-1.5">
            <span className="truncate">{task.request.selected_repository}</span>
            {task.request.selected_branch && (
              <span className="text-neutral-500">
                / {task.request.selected_branch}
              </span>
            )}
          </div>
        )}
        {task.detail && (
          <div className="text-xs text-neutral-500 truncate">{task.detail}</div>
        )}
        <div className="text-xs text-neutral-500">
          {new Date(task.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
