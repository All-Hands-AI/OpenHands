import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { GitControlBarRepoButton } from "./git-control-bar-repo-button";
import { GitControlBarBranchButton } from "./git-control-bar-branch-button";
import { GitControlBarPullButton } from "./git-control-bar-pull-button";
import { GitControlBarPushButton } from "./git-control-bar-push-button";
import { GitControlBarPrButton } from "./git-control-bar-pr-button";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { Provider } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";
import { GitControlBarTooltipWrapper } from "./git-control-bar-tooltip-wrapper";

interface GitControlBarProps {
  onSuggestionsClick: (value: string) => void;
  isWaitingForUserInput: boolean;
  hasSubstantiveAgentActions: boolean;
  optimisticUserMessage: boolean;
}

export function GitControlBar({
  onSuggestionsClick,
  isWaitingForUserInput,
  hasSubstantiveAgentActions,
  optimisticUserMessage,
}: GitControlBarProps) {
  const { t } = useTranslation();

  const { data: conversation } = useActiveConversation();

  const selectedRepository = conversation?.selected_repository;
  const gitProvider = conversation?.git_provider as Provider;
  const selectedBranch = conversation?.selected_branch;

  // Button is enabled when the agent is waiting for user input, has substantive actions, and no optimistic message
  const isButtonEnabled =
    isWaitingForUserInput &&
    hasSubstantiveAgentActions &&
    !optimisticUserMessage;

  const hasRepository = !!selectedRepository;

  const tooltipMessage = useMemo(() => {
    if (!hasRepository) {
      return t(I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT);
    }

    if (!isWaitingForUserInput) {
      return t(
        I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT_WAITING_FOR_USER_INPUT,
      );
    }

    if (!hasSubstantiveAgentActions) {
      return t(
        I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT_HAS_SUBSTANTIVE_AGENT_ACTIONS,
      );
    }

    if (optimisticUserMessage) {
      return t(
        I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT_OPTIMISTIC_USER_MESSAGE,
      );
    }

    return "";
  }, [
    hasRepository,
    t,
    isWaitingForUserInput,
    hasSubstantiveAgentActions,
    optimisticUserMessage,
  ]);

  const shouldShowTooltipForGitActions = !!tooltipMessage;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-row gap-2.5 items-center flex-wrap">
        <GitControlBarTooltipWrapper
          tooltipMessage={t(I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT)}
          testId="git-control-bar-repo-button-tooltip"
          shouldShowTooltip={!hasRepository}
        >
          <GitControlBarRepoButton
            selectedRepository={selectedRepository}
            gitProvider={gitProvider}
          />
        </GitControlBarTooltipWrapper>

        <GitControlBarTooltipWrapper
          tooltipMessage={t(I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT)}
          testId="git-control-bar-branch-button-tooltip"
          shouldShowTooltip={!hasRepository}
        >
          <GitControlBarBranchButton
            selectedBranch={selectedBranch}
            selectedRepository={selectedRepository}
            gitProvider={gitProvider}
          />
        </GitControlBarTooltipWrapper>
      </div>

      <div className="flex flex-row gap-2.5 items-center flex-wrap">
        <GitControlBarTooltipWrapper
          tooltipMessage={tooltipMessage}
          testId="git-control-bar-pull-button-tooltip"
          shouldShowTooltip={shouldShowTooltipForGitActions}
        >
          <GitControlBarPullButton
            onSuggestionsClick={onSuggestionsClick}
            isEnabled={isButtonEnabled}
          />
        </GitControlBarTooltipWrapper>

        <GitControlBarTooltipWrapper
          tooltipMessage={tooltipMessage}
          testId="git-control-bar-push-button-tooltip"
          shouldShowTooltip={shouldShowTooltipForGitActions}
        >
          <GitControlBarPushButton
            onSuggestionsClick={onSuggestionsClick}
            isEnabled={isButtonEnabled}
            hasRepository={hasRepository}
            currentGitProvider={gitProvider}
          />
        </GitControlBarTooltipWrapper>

        <GitControlBarTooltipWrapper
          tooltipMessage={tooltipMessage}
          testId="git-control-bar-pr-button-tooltip"
          shouldShowTooltip={shouldShowTooltipForGitActions}
        >
          <GitControlBarPrButton
            onSuggestionsClick={onSuggestionsClick}
            isEnabled={isButtonEnabled}
            hasRepository={hasRepository}
            currentGitProvider={gitProvider}
          />
        </GitControlBarTooltipWrapper>
      </div>
    </div>
  );
}
