import React from "react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { searchPublicRepositories } from "#/api/github";

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
  const [searchedRepo, setSearchedRepo] =
    React.useState<GitHubRepository | null>(null);

  React.useEffect(() => {
    const searchPublicRepo = async () => {
      const repos = await searchPublicRepositories(searchQuery);
      setSearchedRepo(repos.length > 0 ? repos[0] : null);
    };

    const debounceTimeout = setTimeout(searchPublicRepo, 300);
    return () => clearTimeout(debounceTimeout);
  }, [searchQuery]);

  // Combine searched repo with existing repositories
  const finalRepositories = [
    ...(searchedRepo
      ? [
          {
            ...searchedRepo,
            fromPublicRepoSearch: true,
          },
        ]
      : []),
    ...repositories,
  ];

  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = finalRepositories.find((r) => r.id.toString() === id);
    if (repo) {
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

  const emptyContent = "No results found.";

  return (
    <Autocomplete
      data-testid="github-repo-selector"
      name="repo"
      aria-label="GitHub Repository"
      placeholder="Select a GitHub project"
      selectedKey={selectedKey}
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
      }}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      onInputChange={(value) => setSearchQuery(value)}
      clearButtonProps={{ onClick: handleClearSelection }}
      listboxProps={{
        emptyContent,
        startContent: config?.APP_MODE === "saas" && config?.APP_SLUG ? (
          <a
            href={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
            target="_blank"
            rel="noreferrer noopener"
            className="block w-full px-2 py-2 text-sm text-blue-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            onClick={(e) => e.stopPropagation()}
          >
            Add more repositories...
          </a>
        ) : undefined,
      }}
      filter={(item, query) => 
        !query || item.full_name.toLowerCase().includes(query.toLowerCase())
      }
    >
      {finalRepositories.map((repo) => (
        <AutocompleteItem
          data-testid="github-repo-item"
          key={repo.id}
          value={repo.id}
          className="data-[selected=true]:bg-default-100"
        >
          {repo.full_name}
          {repo.fromPublicRepoSearch && repo.stargazers_count !== undefined && (
            <span className="ml-1 text-gray-400">({repo.stargazers_count}⭐)</span>
          )}
        </AutocompleteItem>
      ))}
    </Autocomplete>
  );
}
