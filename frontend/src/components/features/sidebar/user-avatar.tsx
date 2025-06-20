import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import ProfileIcon from "#/icons/profile.svg?react";
import { cn } from "#/utils/utils";
import { Avatar } from "./avatar";
// import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

interface UserAvatarProps {
  onClick: () => void;
  avatarUrl?: string;
  isLoading?: boolean;
}

export function UserAvatar({ onClick, avatarUrl, isLoading }: UserAvatarProps) {
  const { t } = useTranslation();
  return (
    <button
      data-testid="user-avatar"
      aria-label={t(I18nKey.USER$ACCOUNT_SETTINGS)}
      onClick={onClick}
      className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center hover:opacity-80",
        isLoading && "bg-transparent",
      )}
    >
      {!isLoading && avatarUrl && <Avatar src={avatarUrl} />}
      {!isLoading && !avatarUrl && (
        <ProfileIcon
          aria-label={t(I18nKey.USER$AVATAR_PLACEHOLDER)}
          width={24}
          height={24}
          className="text-[#9099AC]"
        />
      )}
      {isLoading && <LoadingSpinner size="small" />}
    </button>
  );
}
