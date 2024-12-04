import posthog from "posthog-js";
import React from "react";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import { useAuth } from "#/context/auth-context";
import { downloadWorkspace } from "#/utils/download-workspace";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ActionSuggestions({
  onSuggestionsClick,
}: ActionSuggestionsProps) {
  const { gitHubToken } = useAuth();

  const [isDownloading, setIsDownloading] = React.useState(false);
  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  const handleDownloadWorkspace = async () => {
    setIsDownloading(true);
    try {
      await downloadWorkspace();
    } catch (error) {
      // TODO: Handle error
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 mb-2">
      {gitHubToken ? (
        <div className="flex flex-row gap-2 justify-center w-full">
          {!hasPullRequest ? (
            <>
              <SuggestionItem
                suggestion={{
                  label: "Push to Branch",
                  value:
                    "Please push the changes to a remote branch on GitHub, but do NOT create a pull request.",
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
                    "Please push the changes to GitHub and open a pull request.",
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
      ) : (
        <SuggestionItem
          suggestion={{
            label: !isDownloading
              ? "Download .zip"
              : "Downloading, please wait...",
            value: "Download .zip",
          }}
          onClick={() => {
            posthog.capture("download_workspace_button_clicked");
            handleDownloadWorkspace();
          }}
        />
      )}
    </div>
  );
}
