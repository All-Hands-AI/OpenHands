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

  return (
    <div className="flex flex-row items-center">
      <div className="flex flex-row gap-2.5 items-center overflow-x-auto flex-wrap md:flex-nowrap relative scrollbar-hide">
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

        {hasRepository ? (
          <>
            <GitControlBarTooltipWrapper
              tooltipMessage={t(I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT)}
              testId="git-control-bar-pull-button-tooltip"
              shouldShowTooltip={!hasRepository}
            >
              <GitControlBarPullButton
                onSuggestionsClick={onSuggestionsClick}
                isEnabled={isButtonEnabled}
              />
            </GitControlBarTooltipWrapper>

            <GitControlBarTooltipWrapper
              tooltipMessage={t(I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT)}
              testId="git-control-bar-push-button-tooltip"
              shouldShowTooltip={!hasRepository}
            >
              <GitControlBarPushButton
                onSuggestionsClick={onSuggestionsClick}
                isEnabled={isButtonEnabled}
                hasRepository={hasRepository}
                currentGitProvider={gitProvider}
              />
            </GitControlBarTooltipWrapper>

            <GitControlBarTooltipWrapper
              tooltipMessage={t(I18nKey.COMMON$GIT_TOOLS_DISABLED_CONTENT)}
              testId="git-control-bar-pr-button-tooltip"
              shouldShowTooltip={!hasRepository}
            >
              <GitControlBarPrButton
                onSuggestionsClick={onSuggestionsClick}
                isEnabled={isButtonEnabled}
                hasRepository={hasRepository}
                currentGitProvider={gitProvider}
              />
            </GitControlBarTooltipWrapper>
          </>
        ) : null}
      </div>
    </div>
  );
}
