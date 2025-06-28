import posthog from "posthog-js";
import React from "react";
import { useTranslation } from "react-i18next";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import { I18nKey } from "#/i18n/declaration";
import { useUserProviders } from "#/hooks/use-user-providers";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useWsClient } from "#/context/ws-client-provider";
import { OpenHandsBaseEvent } from "#/types/core/base";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ActionSuggestions({
  onSuggestionsClick,
}: ActionSuggestionsProps) {
  const { t } = useTranslation();
  const { providers } = useUserProviders();
  const { data: conversation } = useActiveConversation();
  const { parsedEvents } = useWsClient();
  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  const providersAreSet = providers.length > 0;
  const isGitLab = providers.includes("gitlab");
  const isBitbucket = providers.includes("bitbucket");

  // Check if there are any non-environment events
  const hasNonEnvironmentEvents = React.useMemo(() => {
    return parsedEvents.some((event: OpenHandsBaseEvent) =>
      event.source !== "environment"
    );
  }, [parsedEvents]);

  const pr = isGitLab ? "merge request" : "pull request";
  const prShort = isGitLab ? "MR" : "PR";

  const getProviderName = () => {
    if (isGitLab) return "GitLab";
    if (isBitbucket) return "Bitbucket";
    return "GitHub";
  };

  const terms = {
    pr,
    prShort,
    pushToBranch: `Please push the changes to a remote branch on ${getProviderName()}, but do NOT create a ${pr}. Check your current branch name first - if it's main, master, deploy, or another common default branch name, create a new branch with a descriptive name related to your changes. Otherwise, use the exact SAME branch name as the one you are currently on.`,
    createPR: `Please push the changes to ${getProviderName()} and open a ${pr}. Please create a meaningful branch name that describes the changes. If a ${pr} template exists in the repository, please follow it when creating the ${prShort} description.`,
    pushToPR: `Please push the latest changes to the existing ${pr}.`,
  };

  return (
    <div className="flex flex-col gap-2 mb-2">
      {providersAreSet && conversation?.selected_repository && hasNonEnvironmentEvents && (
        <div className="flex flex-row gap-2 justify-center w-full">
          {!hasPullRequest ? (
            <>
              <SuggestionItem
                suggestion={{
                  label: t(I18nKey.ACTION$PUSH_TO_BRANCH),
                  value: terms.pushToBranch,
                }}
                onClick={(value) => {
                  posthog.capture("push_to_branch_button_clicked");
                  onSuggestionsClick(value);
                }}
              />
              <SuggestionItem
                suggestion={{
                  label: t(I18nKey.ACTION$PUSH_CREATE_PR),
                  value: terms.createPR,
                }}
                onClick={(value) => {
                  posthog.capture("create_pr_button_clicked");
                  onSuggestionsClick(value);
                  setHasPullRequest(true);
                }}
              />
            </>
          ) : (
            <SuggestionItem
              suggestion={{
                label: t(I18nKey.ACTION$PUSH_CHANGES_TO_PR),
                value: terms.pushToPR,
              }}
              onClick={(value) => {
                posthog.capture("push_to_pr_button_clicked");
                onSuggestionsClick(value);
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}
