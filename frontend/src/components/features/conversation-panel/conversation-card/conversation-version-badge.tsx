import { Tooltip } from "@heroui/react";
import { cn } from "#/utils/utils";

interface ConversationVersionBadgeProps {
  version?: "V0" | "V1";
  isConversationArchived?: boolean;
}

export function ConversationVersionBadge({
  version,
  isConversationArchived,
}: ConversationVersionBadgeProps) {
  if (!version) return null;

  const tooltipText =
    version === "V1"
      ? "Conversation API Version 1 (New)"
      : "Conversation API Version 0 (Legacy)";

  return (
    <Tooltip content={tooltipText} placement="top">
      <span
        className={cn(
          "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 cursor-help lowercase",
          version === "V1"
            ? "bg-green-500/20 text-green-500"
            : "bg-neutral-500/20 text-neutral-400",
          isConversationArchived && "opacity-60",
        )}
      >
        {version}
      </span>
    </Tooltip>
  );
}
