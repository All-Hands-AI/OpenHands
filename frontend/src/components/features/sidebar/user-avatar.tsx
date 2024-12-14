import { LoadingSpinner } from "#/components/shared/loading-spinner";
import DefaultUserAvatar from "#/icons/default-user.svg?react";
import { cn } from "#/utils/utils";
import { Avatar } from "./avatar";

interface UserAvatarProps {
  onClick: () => void;
  avatarUrl?: string;
  isLoading?: boolean;
}

export function UserAvatar({ onClick, avatarUrl, isLoading }: UserAvatarProps) {
  return (
    <button
      data-testid="user-avatar"
      type="button"
      onClick={onClick}
      className={cn(
        "bg-white w-8 h-8 rounded-full flex items-center justify-center",
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
    </button>
  );
}
