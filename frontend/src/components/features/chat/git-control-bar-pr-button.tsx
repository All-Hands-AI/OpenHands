import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import PRIcon from "#/icons/u-pr.svg?react";
import { cn, getCreatePRPrompt } from "#/utils/utils";
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
  const isButtonEnabled = isEnabled && providersAreSet && hasRepository;

  const handlePrClick = () => {
    posthog.capture("create_pr_button_clicked");
    onSuggestionsClick(getCreatePRPrompt(currentGitProvider));
  };

  return (
    <button
      type="button"
      onClick={handlePrClick}
      disabled={!isButtonEnabled}
      className={cn(
        "flex flex-row gap-1 items-center justify-center px-2 py-1 rounded-[100px] w-[126px] min-w-[126px] h-7",
        isButtonEnabled
          ? "bg-[#25272D] hover:bg-[#454545] cursor-pointer"
          : "bg-[rgba(71,74,84,0.50)] cursor-not-allowed",
      )}
    >
      <div className="w-3 h-3 flex items-center justify-center">
        <PRIcon width={12} height={12} color="white" />
      </div>
      <div
        className="font-normal text-white text-sm leading-5 max-w-[126px] truncate"
        title={t(I18nKey.COMMON$PULL_REQUEST)}
      >
        {t(I18nKey.COMMON$PULL_REQUEST)}
      </div>
    </button>
  );
}
