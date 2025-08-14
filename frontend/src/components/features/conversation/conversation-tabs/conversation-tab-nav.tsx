import { ComponentType } from "react";
import { cn } from "#/utils/utils";

type ConversationTabNavProps = {
  icon: ComponentType<{ className: string }>;
  onClick(): void;
  isActive?: boolean;
};

export function ConversationTabNav({
  icon: Icon,
  onClick,
  isActive,
}: ConversationTabNavProps) {
  return (
    <button
      type="button"
      onClick={() => {
        onClick();
      }}
      className={cn(
        "p-1 rounded-md cursor-pointer",
        "text-[#9299AA] bg-[#0D0F11]",
        isActive && "bg-[#25272D]",
        isActive
          ? "hover:text-white hover:bg-tertiary"
          : "hover:text-white hover:bg-[#0D0F11]",
        isActive
          ? "focus-within:text-white focus-within:bg-tertiary"
          : "focus-within:text-white focus-within:bg-[#0D0F11]",
      )}
    >
      <Icon className={cn("w-5 h-5 text-inherit")} />
    </button>
  );
}
