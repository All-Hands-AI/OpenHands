import { useDispatch, useSelector } from "react-redux";
import BlockDrawerLeftIcon from "#/icons/block-drawer-left.svg?react";
import { setIsRightPanelShown } from "#/state/conversation-slice";
import { RootState } from "#/store";

export function ChatActions() {
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const dispatch = useDispatch();

  return (
    <div className="flex items-center justify-end">
      <div
        className="flex items-center justify-center w-[26px] h-[26px] rounded-lg hover:bg-tertiary cursor-pointer"
        onClick={() => {
          dispatch(setIsRightPanelShown(!isRightPanelShown));
        }}
      >
        <BlockDrawerLeftIcon width={18} height={18} />
      </div>
    </div>
  );
}
