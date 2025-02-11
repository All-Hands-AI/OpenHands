import WarningIcon from "#/icons/warning.svg?react";
import SuccessIcon from "#/icons/success.svg?react";

interface KeyStatusIconProps {
  isSet: boolean;
}

export function KeyStatusIcon({ isSet }: KeyStatusIconProps) {
  return (
    <span data-testid={isSet ? "set-indicator" : "unset-indicator"}>
      {isSet ? <SuccessIcon /> : <WarningIcon />}
    </span>
  );
}
