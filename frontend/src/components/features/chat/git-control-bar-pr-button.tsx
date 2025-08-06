import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import PRIcon from "#/icons/u-pr.svg?react";
import { cn } from "#/utils/utils";
import { useUserProviders } from "#/hooks/use-user-providers";
import { I18nKey } from "#/i18n/declaration";
import { Provider } from "#/types/settings";

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
    <button
      type="button"
      onClick={handlePrClick}
      disabled={!isButtonEnabled}
      className={cn(
        "flex flex-row gap-[11px] items-center justify-center px-2 py-1 rounded-[100px] w-[126px] h-7",
        isButtonEnabled
          ? "bg-[#25272D] hover:bg-[#525662] cursor-pointer"
          : "bg-[rgba(71,74,84,0.50)] cursor-not-allowed",
      )}
    >
      <div className="w-3 h-3 flex items-center justify-center">
        <PRIcon width={12} height={12} color="white" />
      </div>
      <div className="font-normal text-white text-sm leading-5">
        {t(I18nKey.COMMON$PULL_REQUEST)}
      </div>
    </button>
  );
}
