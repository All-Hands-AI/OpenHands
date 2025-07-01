import { useTranslation } from "react-i18next";
import { SelectedRepository } from "#/api/open-hands.types";
import { I18nKey } from "#/i18n/declaration";

interface ConversationRepoLinkProps {
  selectedRepository: SelectedRepository;
  variant: "compact" | "default";
}

export function ConversationRepoLink({
  selectedRepository,
  variant = "default",
}: ConversationRepoLinkProps) {
  const { t } = useTranslation();

  if (variant === "compact") {
    return (
      <span
        data-testid="conversation-card-selected-repository"
        className="text-xs text-neutral-400"
      >
        {selectedRepository.selected_repository}
      </span>
    );
  }

  return (
    <div className="flex flex-col">
      <span
        data-testid="conversation-card-selected-repository"
        className="text-xs text-neutral-400"
      >
        {t(I18nKey.CONVERSATION$REPOSITORY)}:{" "}
        {selectedRepository.selected_repository}
      </span>
      <span
        data-testid="conversation-card-selected-branch"
        className="text-xs text-neutral-400"
      >
        {t(I18nKey.CONVERSATION$BRANCH)}: {selectedRepository.selected_branch}
      </span>
      <span
        data-testid="conversation-card-selected-git-provider"
        className="text-xs text-neutral-400"
      >
        {t(I18nKey.CONVERSATION$GIT_PROVIDER)}:{" "}
        {selectedRepository.git_provider}
      </span>
    </div>
  );
}
