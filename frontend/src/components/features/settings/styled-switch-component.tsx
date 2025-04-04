import { cn } from "#/utils/utils";

interface StyledSwitchComponentProps {
  isToggled: boolean;
}

export function StyledSwitchComponent({
  isToggled,
}: StyledSwitchComponentProps) {
  return (
    <div
      className={cn(
        "w-9 h-5 rounded-full flex items-center p-[2px] cursor-pointer",
        isToggled && "justify-end bg-primary ",
        !isToggled && "justify-start bg-[#1E1E1F]",
      )}
    >
      <div className="w-4 h-4 rounded-full bg-white" />
    </div>
  );
}
