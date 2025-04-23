import React from "react";
import { EllipsisButton } from "../conversation-panel/ellipsis-button";
import { ConversationCardContextMenu } from "../conversation-panel/conversation-card-context-menu";
import { useUpdateConversation } from "#/hooks/mutation/use-update-conversation";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversation } from "#/context/conversation-context";

export function ChatHeader() {
  const { conversationId } = useConversation();
  const { data: conversation } = useUserConversation(conversationId || null);
  const { mutate: updateConversation } = useUpdateConversation();

  const [contextMenuVisible, setContextMenuVisible] = React.useState(false);
  const [titleMode, setTitleMode] = React.useState<"view" | "edit">("view");
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleChangeTitle = (title: string) => {
    if (conversationId && title !== conversation?.title) {
      updateConversation({
        id: conversationId,
        conversation: { title },
      });
    }
  };

  const handleBlur = () => {
    if (inputRef.current?.value) {
      const trimmed = inputRef.current.value.trim();
      handleChangeTitle(trimmed);
      inputRef.current!.value = trimmed;
    } else {
      // reset the value if it's empty
      inputRef.current!.value = conversation?.title || "";
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

  const handleEdit = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setTitleMode("edit");
    setContextMenuVisible(false);
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
    <div className="flex items-center justify-between w-full px-4 py-2 border-b border-neutral-600">
      <div className="flex items-center gap-2 flex-1 min-w-0 overflow-hidden mr-2">
        {titleMode === "edit" && (
          <input
            ref={inputRef}
            data-testid="chat-header-title-input"
            onClick={handleInputClick}
            onBlur={handleBlur}
            onKeyUp={handleKeyUp}
            type="text"
            defaultValue={conversation.title}
            className="text-sm leading-6 font-semibold bg-transparent w-full"
          />
        )}
        {titleMode === "view" && (
          <h1
            data-testid="chat-header-title"
            className="text-sm leading-6 font-semibold bg-transparent truncate overflow-hidden"
            title={conversation.title}
          >
            {conversation.title}
          </h1>
        )}
      </div>

      <div className="flex items-center">
        <div className="pl-2">
          <EllipsisButton
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setContextMenuVisible((prev) => !prev);
            }}
          />
        </div>
        <div className="relative">
          {contextMenuVisible && (
            <ConversationCardContextMenu
              onClose={() => setContextMenuVisible(false)}
              onEdit={handleEdit}
              position="bottom"
            />
          )}
        </div>
      </div>
    </div>
  );
}
