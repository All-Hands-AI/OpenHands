import posthog from "posthog-js";
import React from "react";
import { useTranslation } from "react-i18next";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import { I18nKey } from "#/i18n/declaration";
import { useUserProviders } from "#/hooks/use-user-providers";
import { useConversation } from "#/context/conversation-context";
import { useUserConversation } from "#/hooks/query/use-user-conversation";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
  // For testing purposes
  conversationIdProp?: string;
  conversationProp?: { selected_repository?: string | null };
}

export function ActionSuggestions({
  onSuggestionsClick,
  conversationIdProp,
  conversationProp,
}: ActionSuggestionsProps) {
  const { t } = useTranslation();
  const { providers } = useUserProviders();

  // Always declare hooks at the top level to follow React rules
  const { data: fetchedConversation } = useUserConversation(
    conversationIdProp || "",
  );

  // Use the conversation context if available, otherwise use props (for testing)
  let conversationId: string | undefined;
  let conversation: { selected_repository?: string | null } | undefined;

  try {
    const conversationContext = useConversation();
    conversationId = conversationIdProp ?? conversationContext.conversationId;

    if (!conversationProp && conversationId) {
      // Use the fetched conversation data
      conversation = fetchedConversation;
    } else {
      conversation = conversationProp;
    }
  } catch (error) {
    // If useConversation throws (outside of provider), use props
    conversationId = conversationIdProp;
    conversation = conversationProp;
  }

  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  const providersAreSet = providers.length > 0;
  const isGitLab = providers.includes("gitlab");

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
      {providersAreSet && conversation?.selected_repository && (
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
