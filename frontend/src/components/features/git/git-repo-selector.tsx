import React from "react";
import { useTranslation } from "react-i18next";
import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
  Spinner,
} from "@heroui/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { I18nKey } from "#/i18n/declaration";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { sanitizeQuery } from "#/utils/sanitize-query";
import { GitRepository } from "#/types/git";
import { Provider, ProviderOptions } from "#/types/settings";

interface GitRepositorySelectorProps {
  onInputChange: (value: string) => void;
  onSelect: () => void;
  userRepositories: GitRepository[];
  publicRepositories: GitRepository[];
  isLoading?: boolean;
}

export function GitRepositorySelector({
  onInputChange,
  onSelect,
  userRepositories,
  publicRepositories,
  isLoading = false,
}: GitRepositorySelectorProps) {
  const { t } = useTranslation();
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);

  const allRepositories: GitRepository[] = [
    ...publicRepositories.filter(
      (repo) => !userRepositories.find((r) => r.id === repo.id),
    ),
    ...userRepositories,
  ];

  // Group repositories by provider
  const groupedUserRepos = userRepositories.reduce<
    Record<Provider, GitRepository[]>
  >(
    (acc, repo) => {
      if (!acc[repo.git_provider]) {
        acc[repo.git_provider] = [];
      }
      acc[repo.git_provider].push(repo);
      return acc;
    },
    {} as Record<Provider, GitRepository[]>,
  );

  const groupedPublicRepos = publicRepositories.reduce<
    Record<Provider, GitRepository[]>
  >(
    (acc, repo) => {
      if (!acc[repo.git_provider]) {
        acc[repo.git_provider] = [];
      }
      acc[repo.git_provider].push(repo);
      return acc;
    },
    {} as Record<Provider, GitRepository[]>,
  );

  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = allRepositories.find((r) => r.id.toString() === id);
    if (repo) {
      dispatch(setSelectedRepository(repo));
      posthog.capture("repository_selected");
      onSelect();
      setSelectedKey(id);
    }
  };

  const handleClearSelection = () => {
    dispatch(setSelectedRepository(null));
  };

  const emptyContent = isLoading ? (
    <div className="flex items-center justify-center py-2">
      <Spinner size="sm" className="mr-2" />
      <span>{t(I18nKey.GITHUB$LOADING_REPOSITORIES)}</span>
    </div>
  ) : (
    t(I18nKey.GITHUB$NO_RESULTS)
  );

  return (
    <Autocomplete
      data-testid="github-repo-selector"
      name="repo"
      aria-label="Git Repository"
      placeholder={t(I18nKey.LANDING$SELECT_GIT_REPO)}
      isVirtualized={false}
      selectedKey={selectedKey}
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
        endContent: isLoading ? <Spinner size="sm" /> : undefined,
      }}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      onInputChange={onInputChange}
      clearButtonProps={{ onPress: handleClearSelection }}
      listboxProps={{
        emptyContent,
      }}
      defaultFilter={(textValue, inputValue) => {
        if (!inputValue) return true;

        const sanitizedInput = sanitizeQuery(inputValue);

        const repo = allRepositories.find((r) => r.full_name === textValue);
        if (!repo) return false;

        const provider = repo.git_provider?.toLowerCase() as Provider;
        const providerKeys = Object.keys(ProviderOptions) as Provider[];

        // If input is exactly "git", show repos from any git-based provider
        if (sanitizedInput === "git") {
          return providerKeys.includes(provider);
        }

        // Provider based typeahead
        for (const p of providerKeys) {
          if (p.startsWith(sanitizedInput)) {
            return provider === p;
          }
        }

        // Default case: check if the repository name matches the input
        return sanitizeQuery(textValue).includes(sanitizedInput);
      }}
    >
      {config?.APP_MODE === "saas" &&
        config?.APP_SLUG &&
        ((
          <AutocompleteItem key="install">
            <a
              href={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
              target="_blank"
              rel="noreferrer noopener"
              onClick={(e) => e.stopPropagation()}
            >
              {t(I18nKey.GITHUB$ADD_MORE_REPOS)}
            </a>
          </AutocompleteItem> // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ) as any)}
      {Object.entries(groupedUserRepos).map(([provider, repos]) =>
        repos.length > 0 ? (
          <AutocompleteSection
            key={`user-${provider}`}
            showDivider
            title={`${t(I18nKey.GITHUB$YOUR_REPOS)} - ${provider}`}
          >
            {repos.map((repo) => (
              <AutocompleteItem
                data-testid="github-repo-item"
                key={repo.id}
                className="data-[selected=true]:bg-default-100"
                textValue={repo.full_name}
              >
                {repo.full_name}
              </AutocompleteItem>
            ))}
          </AutocompleteSection>
        ) : null,
      )}
      {Object.entries(groupedPublicRepos).map(([provider, repos]) =>
        repos.length > 0 ? (
          <AutocompleteSection
            key={`public-${provider}`}
            showDivider
            title={`${t(I18nKey.GITHUB$PUBLIC_REPOS)} - ${provider}`}
          >
            {repos.map((repo) => (
              <AutocompleteItem
                data-testid="github-repo-item"
                key={repo.id}
                className="data-[selected=true]:bg-default-100"
                textValue={repo.full_name}
              >
                {repo.full_name}
                <span className="ml-1 text-gray-400">
                  ({repo.stargazers_count || 0}⭐)
                </span>
              </AutocompleteItem>
            ))}
          </AutocompleteSection>
        ) : null,
      )}
    </Autocomplete>
  );
}
