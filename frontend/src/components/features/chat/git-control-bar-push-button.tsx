import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import ArrowUpIcon from "#/icons/u-arrow-up.svg?react";
import { cn, getGitPushPrompt } from "#/utils/utils";
import { useUserProviders } from "#/hooks/use-user-providers";
import { I18nKey } from "#/i18n/declaration";
import { Provider } from "#/types/settings";

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
  const isButtonEnabled = isEnabled && providersAreSet && hasRepository;

  const handlePushClick = () => {
    posthog.capture("push_button_clicked");
    onSuggestionsClick(getGitPushPrompt(currentGitProvider));
  };

  return (
    <button
      type="button"
      onClick={handlePushClick}
      disabled={!isButtonEnabled}
      className={cn(
        "flex flex-row gap-1 items-center justify-center px-0.5 py-1 rounded-[100px] w-[77px]",
        isButtonEnabled
          ? "bg-[#25272D] hover:bg-[#525662] cursor-pointer"
          : "bg-[rgba(71,74,84,0.50)] cursor-not-allowed",
      )}
    >
      <div className="w-3 h-3 flex items-center justify-center">
        <ArrowUpIcon width={12} height={12} color="white" />
      </div>
      <div className="font-normal text-white text-sm leading-5">
        {t(I18nKey.COMMON$PUSH)}
      </div>
    </button>
  );
}
