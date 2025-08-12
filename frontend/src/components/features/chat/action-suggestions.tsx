import posthog from "posthog-js";
import React from "react";
import { useTranslation } from "react-i18next";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";
import { I18nKey } from "#/i18n/declaration";
import { useUserProviders } from "#/hooks/use-user-providers";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import {
  getGitPushPrompt,
  getCreatePRPrompt,
  getPushToPRPrompt,
  getPR,
  getPRShort,
} from "#/utils/utils";
import { Provider } from "#/types/settings";

interface ActionSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ActionSuggestions({
  onSuggestionsClick,
}: ActionSuggestionsProps) {
  const { t } = useTranslation();
  const { providers } = useUserProviders();
  const { data: conversation } = useActiveConversation();
  const [hasPullRequest, setHasPullRequest] = React.useState(false);

  const providersAreSet = providers.length > 0;

  // Use the git_provider from the conversation, not the user's authenticated providers
  const currentGitProvider = conversation?.git_provider as Provider;

  const terms = {
    pr: getPR(currentGitProvider === "gitlab"),
    prShort: getPRShort(currentGitProvider === "gitlab"),
    pushToBranch: getGitPushPrompt(currentGitProvider),
    createPR: getCreatePRPrompt(currentGitProvider),
    pushToPR: getPushToPRPrompt(currentGitProvider),
  };

  return (
    <div className="flex flex-col gap-2 mb-2">
      {providersAreSet && conversation?.selected_repository && (
        <div className="flex flex-row gap-2 w-full">
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
