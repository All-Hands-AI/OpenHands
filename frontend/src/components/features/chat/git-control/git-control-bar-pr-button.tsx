import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import PRIcon from "#/icons/u-pr.svg?react";
import { useUserProviders } from "#/hooks/use-user-providers";
import { I18nKey } from "#/i18n/declaration";
import { Provider } from "#/types/settings";
import { GitControlButton } from "./git-control-button";

interface GitControlBarPrButtonProps {
  onSuggestionsClick: (value: string) => void;
  isEnabled: boolean;
  hasRepository: boolean;
  currentGitProvider: Provider;
}

export function GitControlBarPrButton({
  onSuggestionsClick,
  isEnabled,
  hasRepository,
  currentGitProvider,
}: GitControlBarPrButtonProps) {
  const { t } = useTranslation();

  const { providers } = useUserProviders();

  const providersAreSet = providers.length > 0;
  const isGitLab = currentGitProvider === "gitlab";
  const isBitbucket = currentGitProvider === "bitbucket";

  const pr = isGitLab ? "merge request" : "pull request";
  const prShort = isGitLab ? "MR" : "PR";

  const getProviderName = () => {
    if (isGitLab) return "GitLab";
    if (isBitbucket) return "Bitbucket";
    return "GitHub";
  };

  const isButtonEnabled = isEnabled && providersAreSet && hasRepository;

  const handlePrClick = () => {
    posthog.capture("create_pr_button_clicked");
    const prPrompt = `Please push the changes to ${getProviderName()} and open a ${pr}. If you're on a default branch (e.g., main, master, deploy), create a new branch with a descriptive name otherwise use the current branch. If a ${pr} template exists in the repository, please follow it when creating the ${prShort} description.`;
    onSuggestionsClick(prPrompt);
  };

  return (
    <GitControlButton
      type="button"
      onClick={handlePrClick}
      size="extra-wide"
      width="large"
      enabled={!!isButtonEnabled}
      icon={<PRIcon width={12} height={12} color="white" />}
      text={t(I18nKey.COMMON$PULL_REQUEST)}
    />
  );
}
