import { Suspense, useMemo } from "react";
import { useWindowSize } from "@uidotdev/usehooks";
import { useSelector } from "react-redux";
import { ConversationTabContent } from "./conversation-tabs/conversation-tab-content";
import { RootState } from "#/store";
import Terminal from "../terminal/terminal";
import { useConversationTabs } from "./conversation-tabs/use-conversation-tabs";
import { ChatInterface } from "../chat/chat-interface";
import { cn } from "#/utils/utils";
import { ResizableTwoPane } from "./ResizableTwoPane";

export function ConversationMain() {
  const { width } = useWindowSize();
  const [{ terminalOpen }] = useConversationTabs();

  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const showResize = (width ?? 0) > 1024;

  const leftItem = useMemo(
    () => (
      <div className={cn("min-h-[494px] h-full overflow-auto")}>
        <ChatInterface />
      </div>
    ),
    [],
  );
  const rightItem = useMemo(() => {
    if (!isRightPanelShown) {
      return null;
    }

    return (
      <div className="flex flex-col flex-1 gap-3 min-h-[494px]">
        <ConversationTabContent />
        {terminalOpen && (
          <Suspense fallback={<div className="h-full" />}>
            <Terminal />
          </Suspense>
        )}
      </div>
    );
  }, [isRightPanelShown]);

  if (!showResize) {
    return (
      <div
        className={cn(
          "grow flex",
          "w-full h-full overflow-y-scroll relative",
          "flex-col gap-3 overflow-auto w-full",
        )}
      >
        {leftItem}
        {rightItem}
      </div>
    );
  }

  return (
    <ResizableTwoPane>
      {leftItem}
      {rightItem ?? <span />}
    </ResizableTwoPane>
  );
}
