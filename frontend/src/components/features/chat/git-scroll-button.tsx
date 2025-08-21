import { ReactNode } from "react";
import { cn } from "#/utils/utils";

interface GitScrollButtonProps {
  direction: "left" | "right";
  onClick: () => void;
  ariaLabel: string;
  children: ReactNode;
}

export function GitScrollButton({
  direction,
  onClick,
  ariaLabel,
  children,
}: GitScrollButtonProps) {
  const isLeft = direction === "left";

  const baseClasses =
    "flex items-center h-[28px] w-[30.6px] min-w-[30.6px] cursor-pointer relative z-10 bg-gradient-to-l from-transparent from-[7.76%] to-[#0D0F11] to-[80.02%]";

  const pseudoCommonElementClasses =
    "before:content-[''] before:absolute before:inset-y-0 before:w-[30px] before:pointer-events-none before:z-[5] before:backdrop-blur-[1px]";

  const pseudoCommonGradientClasses =
    "before:from-[rgba(13,15,17,0.98)] before:from-0% before:via-[rgba(13,15,17,0.85)] before:via-[25%] before:via-[rgba(13,15,17,0.6)] before:via-[50%] before:via-[rgba(13,15,17,0.2)] before:via-[80%] before:to-transparent before:to-[100%]";

  const pseudoElementClasses = isLeft
    ? "justify-start before:right-[-30px] before:bg-gradient-to-r"
    : "justify-end before:left-[-30px] before:bg-gradient-to-l";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        baseClasses,
        pseudoCommonElementClasses,
        pseudoCommonGradientClasses,
        pseudoElementClasses,
      )}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  );
}
