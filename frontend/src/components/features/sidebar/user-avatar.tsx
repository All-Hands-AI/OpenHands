import { LoadingSpinner } from "#/components/shared/loading-spinner";
import DefaultUserAvatar from "#/icons/default-user.svg?react";
import { cn } from "#/utils/utils";
import { Avatar } from "./avatar";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

interface UserAvatarProps {
  onClick: () => void;
  avatarUrl?: string;
  isLoading?: boolean;
}

export function UserAvatar({ onClick, avatarUrl, isLoading }: UserAvatarProps) {
  return (
    <TooltipButton
      testId="user-avatar"
      tooltip="Account settings"
      ariaLabel="Account settings"
      onClick={onClick}
      className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center border-2 border-gray-200",
        isLoading && "bg-transparent",
      )}
    >
      {!isLoading && avatarUrl && <Avatar src={avatarUrl} />}
      {!isLoading && !avatarUrl && (
        <DefaultUserAvatar
          aria-label="user avatar placeholder"
          width={20}
          height={20}
        />
      )}
      {isLoading && <LoadingSpinner size="small" />}
    </TooltipButton>
  );
}
