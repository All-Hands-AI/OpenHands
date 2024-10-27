import { useTranslation } from "react-i18next";
import { LoadingSpinner } from "./modals/LoadingProject";
import DefaultUserAvatar from "#/assets/default-user.svg?react";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";

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
      type="button"
      onClick={onClick}
      className={cn(
        "bg-white w-8 h-8 rounded-full flex items-center justify-center",
        isLoading && "bg-transparent",
      )}
    >
      {!isLoading && avatarUrl && (
        <img
          src={avatarUrl}
          alt={t(I18nKey.USER_AVATAR)}
          className="w-full h-full rounded-full"
        />
      )}
      {!isLoading && !avatarUrl && (
        <DefaultUserAvatar
          aria-label={t(I18nKey.USER_AVATAR)}
          width={20}
          height={20}
        />
      )}
      {isLoading && <LoadingSpinner size="small" />}
    </button>
  );
}
