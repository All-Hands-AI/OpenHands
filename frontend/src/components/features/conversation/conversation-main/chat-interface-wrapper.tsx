import { cn } from "#/utils/utils";
import { ChatInterface } from "../../chat/chat-interface";

interface ChatInterfaceWrapperProps {
  isRightPanelShown: boolean;
}

export function ChatInterfaceWrapper({
  isRightPanelShown,
}: ChatInterfaceWrapperProps) {
  return (
    <div className="flex justify-center w-full h-full">
      <div
        className={cn(
          "w-full transition-all duration-300 ease-in-out",
          isRightPanelShown ? "max-w-4xl" : "max-w-6xl",
        )}
      >
        <ChatInterface />
      </div>
    </div>
  );
}
