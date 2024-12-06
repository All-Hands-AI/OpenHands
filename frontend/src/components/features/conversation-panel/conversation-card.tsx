import React from "react";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationRepoLink } from "./conversation-repo-link";
import {
  ProjectState,
  ConversationStateIndicator,
} from "./conversation-state-indicator";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { EllipsisButton } from "./ellipsis-button";

interface ProjectCardProps {
  onClick: () => void;
  onDelete: () => void;
  onChangeTitle: (title: string) => void;
  name: string;
  repo: string | null;
  lastUpdated: string; // ISO 8601
  state?: ProjectState;
}

export function ConversationCard({
  onClick,
  onDelete,
  onChangeTitle,
  name,
  repo,
  lastUpdated,
  state = "cold",
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
      inputRef.current!.value = name;
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
      className="h-[100px] w-full px-[18px] py-4 border-b border-neutral-600"
    >
      <div className="flex items-center justify-between">
        <input
          ref={inputRef}
          data-testid="conversation-card-title"
          onClick={handleInputClick}
          onBlur={handleBlur}
          type="text"
          defaultValue={name}
          className="text-sm leading-6 font-semibold bg-transparent"
        />

        <div className="flex items-center gap-2 relative">
          <ConversationStateIndicator state={state} />
          <EllipsisButton
            onClick={(event) => {
              event.stopPropagation();
              setContextMenuVisible((prev) => !prev);
            }}
          />
          {contextMenuVisible && (
            <ContextMenu testId="context-menu" className="absolute left-full">
              <ContextMenuListItem
                testId="delete-button"
                onClick={handleDelete}
              >
                Delete
              </ContextMenuListItem>
            </ContextMenu>
          )}
        </div>
      </div>
      {repo && (
        <ConversationRepoLink
          repo={repo}
          onClick={(e) => e.stopPropagation()}
        />
      )}
      <p className="text-xs text-neutral-400">
        <time>{formatTimeDelta(new Date(lastUpdated))} ago</time>
      </p>
    </div>
  );
}
