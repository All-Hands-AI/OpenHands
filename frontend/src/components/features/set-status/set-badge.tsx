import { cn } from "@nextui-org/react";

interface SetBadgeProps {
  isSet: boolean;
}

export function SetBadge({ isSet }: SetBadgeProps) {
  return (
    <span
      className={cn(
        "text-[11px] leading-4 font-bold uppercase border px-1 rounded text-white",
        !isSet ? "border-red-800 bg-red-500" : "border-green-800 bg-green-500",
      )}
    >
      {isSet ? "set" : "unset"}
    </span>
  );
}
