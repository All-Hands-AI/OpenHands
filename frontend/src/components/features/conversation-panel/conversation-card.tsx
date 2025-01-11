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

interface ConversationCardProps {
  onClick?: () => void;
  onDelete?: () => void;
  onChangeTitle?: (title: string) => void;
  onDownloadWorkspace?: () => void;
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
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onDelete?.();
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

  React.useEffect(() => {
    if (titleMode === "edit") {
      inputRef.current?.focus();
    }
  }, [titleMode]);

  const hasContextMenu = !!(onDelete || onChangeTitle || onDownloadWorkspace);

  return (
    <div
      data-testid="conversation-card"
      onClick={onClick}
      className={cn(
        "h-[100px] w-full px-[18px] py-4 border-b border-neutral-600 cursor-pointer",
        variant === "compact" &&
          "h-auto w-fit rounded-xl border border-[#525252]",
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 w-full">
          {isActive && <span className="w-2 h-2 bg-blue-500 rounded-full" />}
          <input
            ref={inputRef}
            disabled={titleMode === "view"}
            data-testid="conversation-card-title"
            onClick={handleInputClick}
            onBlur={handleBlur}
            onKeyUp={handleKeyUp}
            type="text"
            defaultValue={title}
            className="text-sm leading-6 font-semibold bg-transparent w-full"
          />
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
          <ConversationRepoLink
            selectedRepository={selectedRepository}
            onClick={(e) => e.stopPropagation()}
          />
        )}
        <p className="text-xs text-neutral-400">
          <time>{formatTimeDelta(new Date(lastUpdatedAt))} ago</time>
        </p>
      </div>
    </div>
  );
}
