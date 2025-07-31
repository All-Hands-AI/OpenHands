import { useMemo } from "react";
import { ConversationStatus } from "#/types/conversation-status";
import { cn } from "#/utils/utils";

interface ConversationStatusIndicatorProps {
  conversationStatus: ConversationStatus;
}

export function ConversationStatusIndicator({
  conversationStatus,
}: ConversationStatusIndicatorProps) {
  const conversationStatusBackgroundColor = useMemo(() => {
    switch (conversationStatus) {
      case "STOPPED":
        return "bg-[#FF684E]";
      case "RUNNING":
        return "bg-[#1FBD53]";
      case "STARTING":
        return "bg-[#ffffff]";
      default:
        return "bg-[#ffffff]";
    }
  }, [conversationStatus]);

  return (
    <div
      className={cn("w-3 h-3 rounded-full", conversationStatusBackgroundColor)}
    />
  );
}
