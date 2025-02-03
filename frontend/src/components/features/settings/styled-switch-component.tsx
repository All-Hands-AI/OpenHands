import { cn } from "@nextui-org/react";

interface StyledSwitchComponentProps {
  isToggled: boolean;
}

export function StyledSwitchComponent({
  isToggled,
}: StyledSwitchComponentProps) {
  return (
    <div
      className={cn(
        "w-12 h-6 rounded-xl flex items-center p-1.5 cursor-pointer",
        isToggled && "justify-end bg-[#C9B974]",
        !isToggled && "justify-start bg-[#1F2228] border border-[#B7BDC2]",
      )}
    >
      <div
        className={cn(
          "bg-[#1F2228] w-3 h-3 rounded-xl",
          isToggled ? "bg-[#1F2228]" : "bg-[#B7BDC2]",
        )}
      />
    </div>
  );
}
