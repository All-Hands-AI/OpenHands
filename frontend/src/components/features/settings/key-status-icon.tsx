import SuccessIcon from "#/icons/success.svg?react";
import { cn } from "#/utils/utils";

interface KeyStatusIconProps {
  isSet: boolean;
}

export function KeyStatusIcon({ isSet }: KeyStatusIconProps) {
  return (
    <span data-testid={isSet ? "set-indicator" : "unset-indicator"}>
      <SuccessIcon
        className={cn(isSet ? "text-[#A5E75E]" : "text-[#E76A5E]")}
      />
    </span>
  );
}
