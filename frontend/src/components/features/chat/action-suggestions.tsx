import posthog from "posthog-js";
import React from "react";
import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import type { RootState } from "#/store";
import { useAuth } from "#/context/auth-context";
import { I18nKey } from "#/i18n/declaration";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ActionSuggestions({
  onSuggestionsClick,
}: ActionSuggestionsProps) {
  const { t } = useTranslation();
  const { providersAreSet } = useAuth();
  const { selectedRepository } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  const isGitLab =
    selectedRepository !== null &&
    selectedRepository.git_provider &&
    selectedRepository.git_provider.toLowerCase() === "gitlab";

  const pr = isGitLab ? "merge request" : "pull request";
  const prShort = isGitLab ? "MR" : "PR";

  const terms = {
    pr,
    prShort,
    pushToBranch: `Please push the changes to a remote branch on ${
      isGitLab ? "GitLab" : "GitHub"
    }, but do NOT create a ${pr}. Please use the exact SAME branch name as the one you are currently on.`,
    createPR: `Please push the changes to ${
      isGitLab ? "GitLab" : "GitHub"
    } and open a ${pr}. Please create a meaningful branch name that describes the changes. If a ${pr} template exists in the repository, please follow it when creating the ${prShort} description.`,
    pushToPR: `Please push the latest changes to the existing ${pr}.`,
  };

  return (
    <div className="flex flex-col gap-2 mb-2">
      {providersAreSet && selectedRepository && (
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
