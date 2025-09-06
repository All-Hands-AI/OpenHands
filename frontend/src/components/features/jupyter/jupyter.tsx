import React from "react";
import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { JupyterCell } from "./jupyter-cell";
import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { I18nKey } from "#/i18n/declaration";
import JupyterLargeIcon from "#/icons/jupyter-large.svg?react";

interface JupyterEditorProps {
  maxWidth: number;
}

export function JupyterEditor({ maxWidth }: JupyterEditorProps) {
  const cells = useSelector((state: RootState) => state.jupyter?.cells ?? []);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const jupyterRef = React.useRef<HTMLDivElement>(null);

  const { t } = useTranslation();

  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const { hitBottom, scrollDomToBottom, onChatBodyScroll } =
    useScrollToBottom(jupyterRef);

  return (
    <>
      {isRuntimeInactive && (
        <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
          {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
        </div>
      )}
      {!isRuntimeInactive && cells.length > 0 && (
        <div className="flex-1 h-full flex flex-col" style={{ maxWidth }}>
          <div
            data-testid="jupyter-container"
            className="flex-1 overflow-y-auto fast-smooth-scroll custom-scrollbar-always rounded-xl"
            ref={jupyterRef}
            onScroll={(e) => onChatBodyScroll(e.currentTarget)}
          >
            {cells.map((cell, index) => (
              <JupyterCell key={index} cell={cell} />
            ))}
          </div>
          {!hitBottom && (
            <div className="sticky bottom-2 flex items-center justify-center">
              <ScrollToBottomButton onClick={scrollDomToBottom} />
            </div>
          )}
        </div>
      )}
      {!isRuntimeInactive && cells.length === 0 && (
        <div className="flex flex-col items-center justify-center w-full h-full p-10 gap-4">
          <JupyterLargeIcon width={113} height={113} color="#A1A1A1" />
          <span className="text-[#8D95A9] text-[19px] font-normal leading-5">
            {t(I18nKey.COMMON$JUPYTER_EMPTY_MESSAGE)}
          </span>
        </div>
      )}
    </>
  );
}
