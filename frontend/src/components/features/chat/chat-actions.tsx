import { useDispatch, useSelector } from "react-redux";
import BlockDrawerLeftIcon from "#/icons/block-drawer-left.svg?react";
import { setIsRightPanelShown } from "#/state/conversation-slice";
import { RootState } from "#/store";
import { cn } from "#/utils/utils";
import { ChatActionTooltip } from "./chat-action-tooltip";

export function ChatActions() {
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const { shouldShownAgentLoading } = useSelector(
    (state: RootState) => state.conversation,
  );

  const dispatch = useDispatch();

  return (
    <div className="flex items-center justify-end gap-x-4">
      <ChatActionTooltip tooltip="Drawer" ariaLabel="Drawer">
        <button
          type="button"
          className={cn(
            "flex items-center justify-center w-[26px] h-[26px] rounded-lg cursor-pointer",
            isRightPanelShown && "bg-[#25272D] hover:bg-tertiary",
            shouldShownAgentLoading && "cursor-not-allowed",
          )}
          onClick={() => {
            if (shouldShownAgentLoading) {
              return;
            }
            dispatch(setIsRightPanelShown(!isRightPanelShown));
          }}
        >
          <BlockDrawerLeftIcon
            width={18}
            height={18}
            className={cn(
              "text-white",
              !isRightPanelShown && "text-[#9299AA] hover:text-white",
            )}
          />
        </button>
      </ChatActionTooltip>
    </div>
  );
}
