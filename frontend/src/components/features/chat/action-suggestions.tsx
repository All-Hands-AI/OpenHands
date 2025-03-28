import posthog from "posthog-js";
import React from "react";
import { useSelector } from "react-redux";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import type { RootState } from "#/store";
import { useAuth } from "#/context/auth-context";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

// Define button configurations to reduce duplication
interface ButtonConfig {
  label: string;
  value: string;
  eventName: string;
  callback?: () => void;
}

export function ActionSuggestions({
  onSuggestionsClick,
}: ActionSuggestionsProps) {
  const { githubTokenIsSet } = useAuth();
  const { selectedRepository } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  // Define the button configurations
  const PUSH_TO_BRANCH: ButtonConfig = {
    label: "Push to Branch",
    value:
      "Please push the changes to a remote branch on GitHub, but do NOT create a pull request. Please use the exact SAME branch name as the one you are currently on.",
    eventName: "push_to_branch_button_clicked",
  };

  const PUSH_AND_CREATE_PR: ButtonConfig = {
    label: "Push & Create PR",
    value:
      "Please push the changes to GitHub and open a pull request. Please create a meaningful branch name that describes the changes.",
    eventName: "create_pr_button_clicked",
    callback: () => setHasPullRequest(true),
  };

  const PUSH_TO_PR: ButtonConfig = {
    label: "Push changes to PR",
    value: "Please push the latest changes to the existing pull request.",
    eventName: "push_to_pr_button_clicked",
  };

  // Helper function to handle button clicks
  const handleButtonClick = (config: ButtonConfig) => {
    posthog.capture(config.eventName);
    onSuggestionsClick(config.value);
    if (config.callback) {
      config.callback();
    }
  };

  return (
    <div className="flex flex-col gap-2 mb-2">
      {githubTokenIsSet && selectedRepository && (
        <div className="flex flex-row gap-2 justify-center w-full">
          {!hasPullRequest ? (
            <>
              <SuggestionItem
                suggestion={{
                  label: PUSH_TO_BRANCH.label,
                  value: PUSH_TO_BRANCH.value,
                }}
                onClick={() => handleButtonClick(PUSH_TO_BRANCH)}
              />
              <SuggestionItem
                suggestion={{
                  label: PUSH_AND_CREATE_PR.label,
                  value: PUSH_AND_CREATE_PR.value,
                }}
                onClick={() => handleButtonClick(PUSH_AND_CREATE_PR)}
              />
            </>
          ) : (
            <SuggestionItem
              suggestion={{
                label: PUSH_TO_PR.label,
                value: PUSH_TO_PR.value,
              }}
              onClick={() => handleButtonClick(PUSH_TO_PR)}
            />
          )}
        </div>
      )}
    </div>
  );
}
