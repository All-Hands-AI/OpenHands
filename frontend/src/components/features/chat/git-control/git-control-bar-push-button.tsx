import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import ArrowUpIcon from "#/icons/u-arrow-up.svg?react";
import { useUserProviders } from "#/hooks/use-user-providers";
import { I18nKey } from "#/i18n/declaration";
import { Provider } from "#/types/settings";
import { GitControlButton } from "./git-control-button";

interface GitControlBarPushButtonProps {
  onSuggestionsClick: (value: string) => void;
  isEnabled: boolean;
  hasRepository: boolean;
  currentGitProvider: Provider;
}

export function GitControlBarPushButton({
  onSuggestionsClick,
  isEnabled,
  hasRepository,
  currentGitProvider,
}: GitControlBarPushButtonProps) {
  const { t } = useTranslation();

  const { providers } = useUserProviders();

  const providersAreSet = providers.length > 0;
  const isGitLab = currentGitProvider === "gitlab";
  const isBitbucket = currentGitProvider === "bitbucket";

  const getProviderName = () => {
    if (isGitLab) return "GitLab";
    if (isBitbucket) return "Bitbucket";
    return "GitHub";
  };

  const isButtonEnabled = isEnabled && providersAreSet && hasRepository;

  const handlePushClick = () => {
    posthog.capture("push_button_clicked");
    const pushPrompt = `Please push the changes to a remote branch on ${getProviderName()}, but do NOT create a pull request. Check your current branch name first - if it's main, master, deploy, or another common default branch name, create a new branch with a descriptive name related to your changes. Otherwise, use the exact SAME branch name as the one you are currently on.`;
    onSuggestionsClick(pushPrompt);
  };

  return (
    <GitControlButton
      type="button"
      onClick={handlePushClick}
      width="medium"
      enabled={!!isButtonEnabled}
      icon={<ArrowUpIcon width={12} height={12} color="white" />}
      text={t(I18nKey.COMMON$PUSH)}
    />
  );
}
