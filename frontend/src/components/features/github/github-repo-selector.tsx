import React from "react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { searchPublicGitHubRepo } from "#/api/github";

interface GitHubRepositorySelectorProps {
  onSelect: () => void;
  repositories: GitHubRepository[];
}

export function GitHubRepositorySelector({
  onSelect,
  repositories,
}: GitHubRepositorySelectorProps) {
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [searchedRepo, setSearchedRepo] = React.useState<GitHubRepository | null>(null);
  const [isSearching, setIsSearching] = React.useState<boolean>(false);

  React.useEffect(() => {
    const searchTimeout = setTimeout(async () => {
      if (searchQuery.trim()) {
        setIsSearching(true);
        try {
          const repo = await searchPublicGitHubRepo(searchQuery);
          setSearchedRepo(repo);
        } catch (error) {
          console.error("Error searching for repo:", error);
        }
        setIsSearching(false);
      } else {
        setSearchedRepo(null);
      }
    }, 500);

    return () => clearTimeout(searchTimeout);
  }, [searchQuery]);

  // Sort repositories by pushed_at
  const sortedRepositories = [...repositories].sort((a, b) => {
    const dateA = a.pushed_at ? new Date(a.pushed_at).getTime() : 0;
    const dateB = b.pushed_at ? new Date(b.pushed_at).getTime() : 0;
    return dateB - dateA;
  });

  // Add option to install app onto more repos and searched repo if found
  const finalRepositories = [
    ...(searchedRepo ? [{
      ...searchedRepo,
      full_name: `${searchedRepo.full_name} (${searchedRepo.stargazers_count} ⭐)`,
    }] : []),
    ...(config?.APP_MODE === "saas" ? [{ id: -1000, full_name: "Add more repositories..." }] : []),
    ...sortedRepositories,
  ];

  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = finalRepositories.find((r) => r.id.toString() === id);
    if (id === "-1000") {
      if (config?.APP_SLUG)
        window.open(
          `https://github.com/apps/${config.APP_SLUG}/installations/new`,
          "_blank",
        );
    } else if (repo) {
      // set query param
      dispatch(setSelectedRepository(repo.full_name));
      posthog.capture("repository_selected");
      onSelect();
      setSelectedKey(id);
    }
  };

  const handleClearSelection = () => {
    // clear query param
    dispatch(setSelectedRepository(null));
  };

  const emptyContent = config?.APP_SLUG ? (
    <a
      href={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
      target="_blank"
      rel="noreferrer noopener"
      className="underline"
    >
      Add more repositories...
    </a>
  ) : (
    "No results found."
  );

  return (
    <Autocomplete
      data-testid="github-repo-selector"
      name="repo"
      aria-label="GitHub Repository"
      placeholder="Select a GitHub project"
      selectedKey={selectedKey}
      inputValue={searchQuery}
      onInputChange={(value) => setSearchQuery(value)}
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
      }}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      clearButtonProps={{ onClick: handleClearSelection }}
      listboxProps={{
        emptyContent: isSearching ? "Searching..." : emptyContent,
      }}
    >
      {finalRepositories.map((repo) => (
        <AutocompleteItem
          data-testid="github-repo-item"
          key={repo.id}
          value={repo.id}
        >
          {repo.full_name}
        </AutocompleteItem>
      ))}
    </Autocomplete>
  );
}
