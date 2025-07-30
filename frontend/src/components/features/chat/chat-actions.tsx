import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import BlockDrawerLeftIcon from "#/icons/block-drawer-left.svg?react";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import { setIsRightPanelShown } from "#/state/conversation-slice";
import { RootState } from "#/store";

export function ChatActions() {
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const { t } = useTranslation();

  const toggleRightPanel = t(I18nKey.CHAT_INTERFACE$TOGGLE_RIGHT_PANEL);

  const dispatch = useDispatch();

  return (
    <div className="flex items-center justify-end">
      <TooltipButton
        tooltip={toggleRightPanel}
        ariaLabel={toggleRightPanel}
        testId="toggle-right-panel-button"
        onClick={() => {
          dispatch(setIsRightPanelShown(!isRightPanelShown));
        }}
        className="cursor-pointer"
      >
        <BlockDrawerLeftIcon width={18} height={18} />
      </TooltipButton>
    </div>
  );
}
