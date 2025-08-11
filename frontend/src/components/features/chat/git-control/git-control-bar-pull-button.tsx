import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import ArrowDownIcon from "#/icons/u-arrow-down.svg?react";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useUserProviders } from "#/hooks/use-user-providers";
import { I18nKey } from "#/i18n/declaration";
import { GitControlButton } from "./git-control-button";

interface GitControlBarPullButtonProps {
  onSuggestionsClick: (value: string) => void;
  isEnabled: boolean;
}

export function GitControlBarPullButton({
  onSuggestionsClick,
  isEnabled,
}: GitControlBarPullButtonProps) {
  const { t } = useTranslation();

  const { data: conversation } = useActiveConversation();
  const { providers } = useUserProviders();

  const providersAreSet = providers.length > 0;
  const hasRepository = conversation?.selected_repository;
  const isButtonEnabled = isEnabled && providersAreSet && hasRepository;

  const handlePullClick = () => {
    posthog.capture("pull_button_clicked");
    onSuggestionsClick("Please pull the latest code from the repository.");
  };

  return (
    <GitControlButton
      type="button"
      onClick={handlePullClick}
      enabled={!!isButtonEnabled}
      icon={<ArrowDownIcon width={12} height={12} color="white" />}
      text={t(I18nKey.COMMON$PULL)}
    />
  );
}
