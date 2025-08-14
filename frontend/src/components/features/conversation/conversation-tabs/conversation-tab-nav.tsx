import { ComponentType } from "react";
import { Tooltip } from "@heroui/react";
import { cn } from "#/utils/utils";

type ConversationTabNavProps = {
  icon: ComponentType<{ className: string }>;
  rightContent?: React.ReactNode;
  onClick(): void;
  isActive?: boolean;
};

export function ConversationTabNav({
  icon: Icon,
  rightContent,
  onClick,
  isActive,
}: ConversationTabNavProps) {
  const showTooltip = !!rightContent;
  const content = () => (
    <button
      type="button"
      onClick={() => {
        onClick();
      }}
      className={cn(
        "p-1 rounded-md",
        "text-[#9299AA] bg-[#0D0F11]",
        isActive && "bg-[#25272D] text-white",
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

  if (showTooltip) {
    return (
      <Tooltip
        showArrow
        content={<div>{rightContent}</div>}
        closeDelay={100}
        placement="right"
        classNames={{
          base: "before:bg-tertiary before:w-4 before:h-4",

          content:
            "p-1 rounded-sm text-[#9299AA] bg-tertiary cursor-pointer hover:text-white",
        }}
      >
        {content()}
      </Tooltip>
    );
  }
  return content();
}
