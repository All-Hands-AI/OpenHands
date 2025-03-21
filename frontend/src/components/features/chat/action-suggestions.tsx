import posthog from "posthog-js";
import React from "react";
import { useSelector } from "react-redux";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import type { RootState } from "#/store";
import { useAuth } from "#/context/auth-context";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ActionSuggestions({
  onSuggestionsClick,
}: ActionSuggestionsProps) {
  const { providersAreSet } = useAuth();
  const { selectedRepository } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  return (
    <div className="flex flex-col gap-2 mb-2">
      {providersAreSet && selectedRepository && (
        <div className="flex flex-row gap-2 justify-center w-full">
          {!hasPullRequest ? (
            <>
              <SuggestionItem
                suggestion={{
                  label: "Push to Branch",
                  value:
                    "Please push the changes to a remote branch on GitHub, but do NOT create a pull request. Please use the exact SAME branch name as the one you are currently on.",
                }}
                onClick={(value) => {
                  posthog.capture("push_to_branch_button_clicked");
                  onSuggestionsClick(value);
                }}
              />
              <SuggestionItem
                suggestion={{
                  label: "Push & Create PR",
                  value:
                    "Please push the changes to GitHub and open a pull request. Please use the exact SAME branch name as the one you are currently on.",
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
                label: "Push changes to PR",
                value:
                  "Please push the latest changes to the existing pull request.",
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
