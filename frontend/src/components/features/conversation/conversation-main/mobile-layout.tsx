import { ChatInterface } from "../../chat/chat-interface";
import { ConversationTabContent } from "../conversation-tabs/conversation-tab-content/conversation-tab-content";
import { cn } from "#/utils/utils";

interface MobileLayoutProps {
  isRightPanelShown: boolean;
}

export function MobileLayout({ isRightPanelShown }: MobileLayoutProps) {
  return (
    <div className="flex flex-col gap-3 overflow-auto w-full">
      <div
        className={cn(
          "overflow-hidden w-full bg-base min-h-[600px]",
          !isRightPanelShown && "h-full",
        )}
      >
        <ChatInterface />
      </div>
      {isRightPanelShown && (
        <div className="h-full w-full min-h-[494px] flex flex-col gap-3">
          <ConversationTabContent />
        </div>
      )}
    </div>
  );
}
