import React from "react";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationRepoLink } from "./conversation-repo-link";
import {
  ProjectStatus,
  ConversationStateIndicator,
} from "./conversation-state-indicator";
import { EllipsisButton } from "./ellipsis-button";
import { ConversationCardContextMenu } from "./conversation-card-context-menu";
import { cn } from "#/utils/utils";
import { BaseModal } from "../../shared/modals/base-modal/base-modal";

interface ConversationCardProps {
  onClick?: () => void;
  onDelete?: () => void;
  onChangeTitle?: (title: string) => void;
  onDownloadWorkspace?: () => void;
  onDisplayCost?: () => void;
  isActive?: boolean;
  title: string;
  selectedRepository: string | null;
  lastUpdatedAt: string; // ISO 8601
  status?: ProjectStatus;
  variant?: "compact" | "default";
}

export function ConversationCard({
  onClick,
  onDelete,
  onChangeTitle,
  onDownloadWorkspace,
  onDisplayCost,
  isActive,
  title,
  selectedRepository,
  lastUpdatedAt,
  status = "STOPPED",
  variant = "default",
}: ConversationCardProps) {
  const [contextMenuVisible, setContextMenuVisible] = React.useState(false);
  const [titleMode, setTitleMode] = React.useState<"view" | "edit">("view");
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Only create metrics-related state if onDisplayCost is provided
  const [metricsModalVisible, setMetricsModalVisible] = React.useState(false);
  const [metrics, setMetrics] = React.useState<{
    cost: number | null;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    } | null;
  }>({
    cost: null,
    usage: null,
  });

  // Only add metrics event listener if onDisplayCost is provided
  React.useEffect(() => {
    if (!onDisplayCost) return () => {};

    function handleMessage(event: MessageEvent) {
      if (event.data?.type === "metrics_update") {
        setMetrics(event.data.metrics);
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [onDisplayCost]);

  const handleBlur = () => {
    if (inputRef.current?.value) {
      const trimmed = inputRef.current.value.trim();
      onChangeTitle?.(trimmed);
      inputRef.current!.value = trimmed;
    } else {
      // reset the value if it's empty
      inputRef.current!.value = title;
    }

    setTitleMode("view");
  };

  const handleKeyUp = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.currentTarget.blur();
    }
  };

  const handleInputClick = (event: React.MouseEvent<HTMLInputElement>) => {
    if (titleMode === "edit") {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onDelete?.();
    setContextMenuVisible(false);
  };

  const handleEdit = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setTitleMode("edit");
    setContextMenuVisible(false);
  };

  const handleDownload = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onDownloadWorkspace?.();
  };

  const handleDisplayCost = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setMetricsModalVisible(true);
    onDisplayCost?.();
  };

  React.useEffect(() => {
    if (titleMode === "edit") {
      inputRef.current?.focus();
    }
  }, [titleMode]);

  const hasContextMenu = !!(
    onDelete ||
    onChangeTitle ||
    onDownloadWorkspace ||
    onDisplayCost
  );

  return (
    <>
      <div
        data-testid="conversation-card"
        onClick={onClick}
        className={cn(
          "h-[100px] w-full px-[18px] py-4 border-b border-neutral-600 cursor-pointer",
          variant === "compact" &&
            "h-auto w-fit rounded-xl border border-[#525252]",
        )}
      >
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2 flex-1 min-w-0 overflow-hidden mr-2">
            {isActive && (
              <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
            )}
            {titleMode === "edit" && (
              <input
                ref={inputRef}
                data-testid="conversation-card-title"
                onClick={handleInputClick}
                onBlur={handleBlur}
                onKeyUp={handleKeyUp}
                type="text"
                defaultValue={title}
                className="text-sm leading-6 font-semibold bg-transparent w-full"
              />
            )}
            {titleMode === "view" && (
              <p
                data-testid="conversation-card-title"
                className="text-sm leading-6 font-semibold bg-transparent truncate overflow-hidden"
                title={title}
              >
                {title}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 relative">
            <ConversationStateIndicator status={status} />
            {hasContextMenu && (
              <EllipsisButton
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  setContextMenuVisible((prev) => !prev);
                }}
              />
            )}
            {contextMenuVisible && (
              <ConversationCardContextMenu
                onClose={() => setContextMenuVisible(false)}
                onDelete={onDelete && handleDelete}
                onEdit={onChangeTitle && handleEdit}
                onDownload={onDownloadWorkspace && handleDownload}
                onDisplayCost={onDisplayCost && handleDisplayCost}
                position={variant === "compact" ? "top" : "bottom"}
              />
            )}
          </div>
        </div>

        <div
          className={cn(
            variant === "compact" && "flex items-center justify-between mt-1",
          )}
        >
          {selectedRepository && (
            <ConversationRepoLink selectedRepository={selectedRepository} />
          )}
          <p className="text-xs text-neutral-400">
            <time>{formatTimeDelta(new Date(lastUpdatedAt))} ago</time>
          </p>
        </div>
      </div>

      {onDisplayCost && (
        <BaseModal
          isOpen={metricsModalVisible}
          onOpenChange={setMetricsModalVisible}
          title="Metrics Information"
          testID="metrics-modal"
        >
          <div className="space-y-2">
            {metrics?.cost !== null && (
              <p>Total Cost: ${metrics.cost.toFixed(4)}</p>
            )}
            {metrics?.usage !== null && (
              <>
                <p>Tokens Used:</p>
                <ul className="list-inside space-y-1 ml-2">
                  <li>- Input: {metrics.usage.prompt_tokens}</li>
                  <li>- Output: {metrics.usage.completion_tokens}</li>
                  <li>- Total: {metrics.usage.total_tokens}</li>
                </ul>
              </>
            )}
            {!metrics?.cost && !metrics?.usage && (
              <p className="text-neutral-400">No metrics data available</p>
            )}
          </div>
        </BaseModal>
      )}
    </>
  );
}
