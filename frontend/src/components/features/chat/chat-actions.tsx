import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import BlockDrawerLeftIcon from "#/icons/block-drawer-left.svg?react";
import PlayIcon from "#/icons/play-solid.svg?react";
import {
  setIsRightPanelShown,
  setMessageToSend,
} from "#/state/conversation-slice";
import { RootState } from "#/store";
import { cn } from "#/utils/utils";
import { ChatActionTooltip } from "./chat-action-tooltip";
import { I18nKey } from "#/i18n/declaration";
import { RUN_SERVER_SUGGESTION } from "#/utils/suggestions/repo-suggestions";

export function ChatActions() {
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const { shouldShownAgentLoading } = useSelector(
    (state: RootState) => state.conversation,
  );

  const dispatch = useDispatch();
  const { t } = useTranslation();

  const onRunClick = () => {
    dispatch(setMessageToSend(RUN_SERVER_SUGGESTION));
  };

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
      <button
        type="button"
        onClick={onRunClick}
        data-testid="run-button"
        className={cn(
          "bg-white py-0.75 pl-2 pr-3.5 rounded-full cursor-pointer",
          `flex flex-row items-center`,
          "text-black",
        )}
      >
        <PlayIcon className="w-4.5 h-4.5 text-inherit" />
        <span className="text-inherit text-sm font-medium">
          {t(I18nKey.CONVERSATION$RUN)}
        </span>
      </button>
    </div>
  );
}
