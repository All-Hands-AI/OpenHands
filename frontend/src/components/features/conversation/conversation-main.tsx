import { Suspense } from "react";
import { useWindowSize } from "@uidotdev/usehooks";
import { useSelector } from "react-redux";
import { ConversationTabContent } from "./conversation-tabs/conversation-tab-content";
import { RootState } from "#/store";
import Terminal from "../terminal/terminal";
import { useConversationTabs } from "./conversation-tabs/use-conversation-tabs";
import { ChatInterface } from "../chat/chat-interface";
import { cn } from "#/utils/utils";

export function ConversationMain() {
  const { width } = useWindowSize();
  const [{ terminalOpen }] = useConversationTabs();

  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  const windowWith = width ?? 0;

  return (
    <div
      className={cn(
        "grow flex",
        windowWith < 1024
          ? "flex-col gap-3 overflow-auto w-full"
          : "flex-row justify-center h-full",
      )}
    >
      <div className={cn("min-h-[494px] overflow-auto")}>
        <ChatInterface />
      </div>
      {isRightPanelShown && (
        <div className="flex flex-col flex-1 gap-3 min-h-[494px]">
          <ConversationTabContent />
          {terminalOpen && (
            <Suspense fallback={<div className="h-full" />}>
              <Terminal />
            </Suspense>
          )}
        </div>
      )}
    </div>
  );
}
