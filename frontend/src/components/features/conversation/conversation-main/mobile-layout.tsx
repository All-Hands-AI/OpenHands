import { ChatInterface } from "../../chat/chat-interface";
import { ConversationTabContent } from "../conversation-tabs/conversation-tab-content/conversation-tab-content";
import { cn } from "#/utils/utils";

interface MobileLayoutProps {
  isRightPanelShown: boolean;
}

export function MobileLayout({ isRightPanelShown }: MobileLayoutProps) {
  return (
    <div className="relative h-full flex flex-col overflow-hidden">
      {/* Chat area - shrinks when panel slides up */}
      <div
        className={cn(
          "flex-1 bg-base overflow-hidden transition-all duration-300 ease-in-out",
          isRightPanelShown ? "flex-[0.6]" : "flex-1",
        )}
      >
        <ChatInterface />
      </div>

      {/* Bottom panel - slides up from bottom */}
      <div
        className={cn(
          "absolute bottom-0 left-0 right-0 transition-all duration-300 ease-in-out overflow-hidden",
          isRightPanelShown
            ? "h-[40%] translate-y-0 opacity-100"
            : "h-0 translate-y-full opacity-0",
        )}
      >
        <div className="h-full flex flex-col gap-3 pt-2">
          <ConversationTabContent />
        </div>
      </div>
    </div>
  );
}
