import { useMemo } from "react";
import { ConversationStatus } from "#/types/conversation-status";
import { cn } from "#/utils/utils";

interface ConversationStatusIndicatorProps {
  conversationStatus: ConversationStatus;
}

export function ConversationStatusIndicator({
  conversationStatus,
}: ConversationStatusIndicatorProps) {
  console.log("conversationStatus", conversationStatus);
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

  console.log(
    "conversationStatusBackgroundColor",
    conversationStatusBackgroundColor,
  );

  return (
    <div
      className={cn("w-3 h-3 rounded-full", conversationStatusBackgroundColor)}
    />
  );
}
