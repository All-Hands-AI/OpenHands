import { cn } from "#/utils/utils";
import { ChatInterfaceWrapper } from "./chat-interface-wrapper";
import { ConversationTabContent } from "../conversation-tabs/conversation-tab-content/conversation-tab-content";

interface DesktopLayoutProps {
  isRightPanelShown: boolean;
}

export function DesktopLayout({ isRightPanelShown }: DesktopLayoutProps) {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex flex-1 transition-all duration-300 ease-in-out overflow-hidden">
        <div className="flex flex-col transition-all duration-300 ease-in-out flex-1 bg-base overflow-hidden">
          <ChatInterfaceWrapper isRightPanelShown={isRightPanelShown} />
        </div>

        <div
          className={cn(
            "transition-all duration-300 ease-in-out overflow-hidden",
            isRightPanelShown
              ? "flex-1 translate-x-0 opacity-100"
              : "w-0 translate-x-full opacity-0",
          )}
        >
          <div className="flex flex-col flex-1 gap-3 min-w-max h-full">
            <ConversationTabContent />
          </div>
        </div>
      </div>
    </div>
  );
}
