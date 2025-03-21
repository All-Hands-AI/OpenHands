import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import { SuggestionBox } from "#/components/features/suggestions/suggestion-box";
import { GitRepositorySelector } from "./github-repo-selector";
import { useAppRepositories } from "#/hooks/query/use-app-repositories";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { sanitizeQuery } from "#/utils/sanitize-query";
import { useDebounce } from "#/hooks/use-debounce";
import { BrandButton } from "../settings/brand-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import { ProviderSelector } from "./providers-selector";
import { Provider } from "#/types/settings";
import { useAuth } from "#/context/auth-context";

interface GitRepositoriesSuggestionBoxProps {
  handleSubmit: () => void;
  gitHubAuthUrl: string | null;
  user: GitHubErrorReponse | GitHubUser | null;
}

export function GitRepositoriesSuggestionBox({
  handleSubmit,
  gitHubAuthUrl,
  user,
}: GitRepositoriesSuggestionBoxProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { providerTokensSet } = useAuth();
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [selectedProvider, setSelectedProvider] =
    React.useState<Provider | null>(
      providerTokensSet.length === 1 ? providerTokensSet[0] : null,
    );

  React.useEffect(() => {
    if (providerTokensSet.length === 1) {
      setSelectedProvider(providerTokensSet[0]);
    } else {
      setSelectedProvider(null);
    }
  }, [providerTokensSet]);

  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  // TODO: Use `useQueries` to fetch all repositories in parallel
  const { data: appRepositories } = useAppRepositories();
  const { data: userRepositories } = useUserRepositories(selectedProvider);
  const { data: searchedRepos } = useSearchRepositories(
    sanitizeQuery(debouncedSearchQuery),
    selectedProvider,
  );

  const repositories =
    userRepositories?.pages.flatMap((page) => page.data) ||
    appRepositories?.pages.flatMap((page) => page.data) ||
    [];

  const handleConnectToGitHub = () => {
    if (gitHubAuthUrl) {
      window.location.href = gitHubAuthUrl;
    } else {
      navigate("/settings");
    }
  };

  const isLoggedIn = !!user;

  return (
    <SuggestionBox
      title={t(I18nKey.LANDING$OPEN_REPO)}
      content={
        isLoggedIn ? (
          <>
            {providerTokensSet.length !== 1 && (
              <ProviderSelector
                selectedProvider={selectedProvider}
                setSelectedProvider={setSelectedProvider}
              />
            )}
            {selectedProvider && (
              <GitRepositorySelector
                onInputChange={setSearchQuery}
                onSelect={handleSubmit}
                publicRepositories={searchedRepos || []}
                userRepositories={repositories}
                selectedProvider={selectedProvider}
              />
            )}
          </>
        ) : (
          <BrandButton
            testId="connect-to-github"
            type="button"
            variant="secondary"
            className="w-full text-content border-content"
            onClick={handleConnectToGitHub}
            startContent={<GitHubLogo width={20} height={20} />}
          >
            {t(I18nKey.GITHUB$CONNECT)}
          </BrandButton>
        )
      }
    />
  );
}
