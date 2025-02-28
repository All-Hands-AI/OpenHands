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
        "w-12 h-6 rounded-xl flex items-center p-1.5 cursor-pointer",
        isToggled && "justify-end bg-primary",
        !isToggled &&
          "justify-start bg-base-secondary border border-tertiary-light",
      )}
    >
      <div
        className={cn(
          "w-3 h-3 rounded-xl",
          isToggled ? "bg-base-secondary" : "bg-tertiary-light",
        )}
      />
    </div>
  );
}
