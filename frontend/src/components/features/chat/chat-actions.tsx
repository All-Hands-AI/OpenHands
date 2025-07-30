import { useDispatch, useSelector } from "react-redux";
import BlockDrawerLeftIcon from "#/icons/block-drawer-left.svg?react";
import { setIsRightPanelShown } from "#/state/conversation-slice";
import { RootState } from "#/store";
import { cn } from "#/utils/utils";

export function ChatActions() {
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const dispatch = useDispatch();

  return (
    <div className="flex items-center justify-end">
      <button
        type="button"
        className={cn(
          "flex items-center justify-center w-[26px] h-[26px] rounded-lg cursor-pointer",
          isRightPanelShown && "bg-[#25272D] hover:bg-tertiary",
        )}
        onClick={() => {
          dispatch(setIsRightPanelShown(!isRightPanelShown));
        }}
      >
        <BlockDrawerLeftIcon
          width={18}
          height={18}
          className={
            isRightPanelShown ? "text-white" : "text-[#9299AA] hover:text-white"
          }
        />
      </button>
    </div>
  );
}
