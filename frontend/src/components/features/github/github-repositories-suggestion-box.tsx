import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SuggestionBox } from "#/components/features/suggestions/suggestion-box";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import { GitHubRepositorySelector } from "./github-repo-selector";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { ConnectToGitHubModal } from "#/components/shared/modals/connect-to-github-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { isGitHubErrorReponse } from "#/api/github-axios-instance";
import { useAppRepositories } from "#/hooks/query/use-app-repositories";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { sanitizeQuery } from "#/utils/sanitize-query";
import { useDebounce } from "#/hooks/use-debounce";

interface GitHubRepositoriesSuggestionBoxProps {
  handleSubmit: () => void;
  gitHubAuthUrl: string | null;
  user: GitHubErrorReponse | GitHubUser | null;
}

export function GitHubRepositoriesSuggestionBox({
  handleSubmit,
  gitHubAuthUrl,
  user,
}: GitHubRepositoriesSuggestionBoxProps) {
  const { t } = useTranslation();
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  // TODO: Use `useQueries` to fetch all repositories in parallel
  const { data: appRepositories } = useAppRepositories();
  const { data: userRepositories } = useUserRepositories();
  const { data: searchedRepos } = useSearchRepositories(
    sanitizeQuery(debouncedSearchQuery),
  );

  const repositories =
    userRepositories?.pages.flatMap((page) => page.data) ||
    appRepositories?.pages.flatMap((page) => page.data) ||
    [];

  const handleConnectToGitHub = () => {
    if (gitHubAuthUrl) {
      window.location.href = gitHubAuthUrl;
    } else {
      setConnectToGitHubModalOpen(true);
    }
  };

  const isLoggedIn = !!user && !isGitHubErrorReponse(user);

  return (
    <>
      <SuggestionBox
        title={t(I18nKey.LANDING$OPEN_REPO)}
        content={
          isLoggedIn ? (
            <GitHubRepositorySelector
              onInputChange={setSearchQuery}
              onSelect={handleSubmit}
              publicRepositories={searchedRepos || []}
              userRepositories={repositories}
            />
          ) : (
            <ModalButton
              text={t(I18nKey.GITHUB$CONNECT)}
              icon={<GitHubLogo width={20} height={20} />}
              className="bg-[#791B80] w-full"
              onClick={handleConnectToGitHub}
            />
          )
        }
      />
      {connectToGitHubModalOpen && (
        <ModalBackdrop onClose={() => setConnectToGitHubModalOpen(false)}>
          <ConnectToGitHubModal
            onClose={() => setConnectToGitHubModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </>
  );
}
