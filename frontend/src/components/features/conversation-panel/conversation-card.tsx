import React from "react";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationRepoLink } from "./conversation-repo-link";
import {
  ProjectStatus,
  ConversationStateIndicator,
} from "./conversation-state-indicator";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { EllipsisButton } from "./ellipsis-button";

interface ProjectCardProps {
  onClick: () => void;
  onDelete: () => void;
  onChangeTitle: (title: string) => void;
  title: string;
  selectedRepository: string | null;
  lastUpdatedAt: string; // ISO 8601
  status?: ProjectStatus;
}

export function ConversationCard({
  onClick,
  onDelete,
  onChangeTitle,
  title,
  selectedRepository,
  lastUpdatedAt,
  status = "STOPPED",
}: ProjectCardProps) {
  const [contextMenuVisible, setContextMenuVisible] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleBlur = () => {
    if (inputRef.current?.value) {
      const trimmed = inputRef.current.value.trim();
      onChangeTitle(trimmed);
      inputRef.current!.value = trimmed;
    } else {
      // reset the value if it's empty
      inputRef.current!.value = title;
    }
  };

  const handleKeyUp = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.currentTarget.blur();
    }
  };

  const handleInputClick = (event: React.MouseEvent<HTMLInputElement>) => {
    event.stopPropagation();
  };

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onDelete();
  };

  return (
    <div
      data-testid="conversation-card"
      onClick={onClick}
      className="h-[100px] w-full px-[18px] py-4 border-b border-neutral-600 cursor-pointer"
    >
      <div className="flex items-center justify-between space-x-1">
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

        <div className="flex items-center gap-2 relative">
          <ConversationStateIndicator status={status} />
          <EllipsisButton
            onClick={(event) => {
              event.stopPropagation();
              setContextMenuVisible((prev) => !prev);
            }}
          />
        </div>
      </div>
      {contextMenuVisible && (
        <ContextMenu testId="context-menu" className="left-full float-right">
          <ContextMenuListItem testId="delete-button" onClick={handleDelete}>
            Delete
          </ContextMenuListItem>
        </ContextMenu>
      )}
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
  );
}
