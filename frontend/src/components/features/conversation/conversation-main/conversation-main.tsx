import { useWindowSize } from "@uidotdev/usehooks";
import { MobileLayout } from "./mobile-layout";
import { DesktopLayout } from "./desktop-layout";
import { useConversationStore } from "#/state/conversation-store";

interface ConversationMainProps {
  isSetupMode?: boolean;
  conversationId?: string;
}

export function ConversationMain({
  isSetupMode,
  conversationId,
}: ConversationMainProps) {
  const { width } = useWindowSize();
  const { isRightPanelShown } = useConversationStore();

  if (width && width <= 1024) {
    return (
      <MobileLayout
        isRightPanelShown={isRightPanelShown}
        isSetupMode={isSetupMode}
        taskId={conversationId}
      />
    );
  }

  return (
    <DesktopLayout
      isRightPanelShown={isRightPanelShown}
      isSetupMode={isSetupMode}
      conversationId={conversationId}
    />
  );
}
