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

  const windowWith = width ?? 0;
  const showResize = windowWith > 1024 && rightItem;

  if (!showResize) {
    return (
      <div
        className={cn(
          "grow flex",
          "w-full h-full overflow-y-scroll relative",
          windowWith < 1024
            ? "flex-col gap-3 overflow-auto w-full"
            : "flex-row justify-center h-full",
        )}
      >
        <div className={cn(windowWith >= 1024 ? "max-w-[768px]" : "")}>
          {leftItem}
        </div>
        {rightItem}
      </div>
    );
  }

  return (
    <ResizableTwoPane>
      {leftItem}
      {rightItem}
    </ResizableTwoPane>
  );
}
