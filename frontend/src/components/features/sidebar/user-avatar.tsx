import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
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
  const { t } = useTranslation();
  return (
    <TooltipButton
      testId="user-avatar"
      tooltip={t(I18nKey.USER$ACCOUNT_SETTINGS)}
      ariaLabel={t(I18nKey.USER$ACCOUNT_SETTINGS)}
      onClick={onClick}
      className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center border-2 border-gray-200",
        isLoading && "bg-transparent",
      )}
    >
      {!isLoading && avatarUrl && <Avatar src={avatarUrl} />}
      {!isLoading && !avatarUrl && (
        <DefaultUserAvatar
          aria-label={t(I18nKey.USER$AVATAR_PLACEHOLDER)}
          width={20}
          height={20}
        />
      )}
      {isLoading && <LoadingSpinner size="small" />}
    </TooltipButton>
  );
}
