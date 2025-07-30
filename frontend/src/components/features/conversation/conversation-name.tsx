import React from "react";
import { useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useUpdateConversation } from "#/hooks/mutation/use-update-conversation";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";
import { EllipsisButton } from "../conversation-panel/ellipsis-button";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";

export function ConversationName() {
  const { t } = useTranslation();
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: conversation } = useActiveConversation();
  const { mutate: updateConversation } = useUpdateConversation();

  const [titleMode, setTitleMode] = React.useState<"view" | "edit">("view");
  const [contextMenuOpen, setContextMenuOpen] = React.useState(true);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const contextMenuRef = useClickOutsideElement<HTMLUListElement>(() =>
    setContextMenuOpen(false),
  );

  const handleDoubleClick = () => {
    setTitleMode("edit");
  };

  const handleBlur = () => {
    if (inputRef.current?.value && conversationId) {
      const trimmed = inputRef.current.value.trim();
      if (trimmed !== conversation?.title) {
        updateConversation(
          { conversationId, newTitle: trimmed },
          {
            onSuccess: () => {
              displaySuccessToast(t(I18nKey.CONVERSATION$TITLE_UPDATED));
            },
          },
        );
      }
      inputRef.current.value = trimmed;
    } else if (inputRef.current) {
      // reset the value if it's empty
      inputRef.current.value = conversation?.title ?? "";
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

  const handleEllipsisClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setContextMenuOpen(!contextMenuOpen);
  };

  const handleRename = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setTitleMode("edit");
    setContextMenuOpen(false);
  };

  React.useEffect(() => {
    if (titleMode === "edit") {
      inputRef.current?.focus();
    }
  }, [titleMode]);

  if (!conversation) {
    return null;
  }

  return (
    <div
      className="flex items-center gap-6 h-[22px] text-base font-normal text-left"
      data-testid="conversation-name"
    >
      {titleMode === "edit" ? (
        <input
          ref={inputRef}
          data-testid="conversation-name-input"
          onClick={handleInputClick}
          onBlur={handleBlur}
          onKeyUp={handleKeyUp}
          type="text"
          defaultValue={conversation.title}
          className="text-white leading-5 bg-transparent border-none outline-none text-base font-normal w-[128px] max-w-[128px]"
        />
      ) : (
        <div
          className="text-white leading-5 cursor-pointer w-[128px] max-w-[128px] truncate"
          data-testid="conversation-name-title"
          onDoubleClick={handleDoubleClick}
          title={conversation.title}
        >
          {conversation.title}
        </div>
      )}

      <div className="relative flex items-center">
        <EllipsisButton fill="#B1B9D3" onClick={handleEllipsisClick} />
        {contextMenuOpen && (
          <ContextMenu
            ref={contextMenuRef}
            testId="conversation-name-context-menu"
            className="absolute left-0 top-full mt-2 z-50 text-white bg-[#525662] rounded-[6px]"
          >
            <ContextMenuListItem
              testId="rename-button"
              onClick={handleRename}
              className="cursor-pointer"
            >
              {t(I18nKey.BUTTON$RENAME)}
            </ContextMenuListItem>
          </ContextMenu>
        )}
      </div>
    </div>
  );
}
