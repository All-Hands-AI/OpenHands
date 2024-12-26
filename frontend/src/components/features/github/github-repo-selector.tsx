import React from "react";
import { Autocomplete, AutocompleteItem, AutocompleteSection } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { searchPublicRepositories } from "#/api/github";
import { useDebounce } from "#/hooks/use-debounce";

interface GitHubRepositoryWithFlag extends GitHubRepository {
  fromPublicRepoSearch?: boolean;
}

interface GitHubRepositorySelectorProps {
  onSelect: () => void;
  repositories: GitHubRepositoryWithFlag[];
}

export function GitHubRepositorySelector({
  onSelect,
  repositories,
}: GitHubRepositorySelectorProps) {
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [searchedRepos, setSearchedRepos] = React.useState<
    GitHubRepositoryWithFlag[]
  >([]);
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  React.useEffect(() => {
    const searchPublicRepo = async () => {
      if (!debouncedSearchQuery) {
        setSearchedRepos([]);
        return;
      }
      const repos = await searchPublicRepositories(debouncedSearchQuery);
      // Sort by stars in descending order
      const sortedRepos = repos
        .sort((a, b) => (b.stargazers_count || 0) - (a.stargazers_count || 0))
        .slice(0, 3)
      setSearchedRepos(sortedRepos);
    };

    searchPublicRepo();
  }, [debouncedSearchQuery]);

  const finalRepositories: GitHubRepositoryWithFlag[] = [
    ...searchedRepos.filter(
      (repo) => !repositories.find((r) => r.id === repo.id),
    ),
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
      }}
      defaultFilter={(textValue, inputValue) =>
        !inputValue ||
        textValue.toLowerCase().includes(inputValue.toLowerCase())
      }
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
              Add more repositories...
            </a>
          </AutocompleteItem> // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ) as any)}
      {repositories.length > 0 && (
        <AutocompleteSection showDivider title="Your Repos">
          {repositories.map((repo) => (
            <AutocompleteItem
              data-testid="github-repo-item"
              key={repo.id}
              value={repo.id}
              className="data-[selected=true]:bg-default-100"
              textValue={repo.full_name}
            >
              {repo.full_name}
            </AutocompleteItem>
          ))}
        </AutocompleteSection>
      )}
      {searchedRepos.length > 0 && (
        <AutocompleteSection showDivider title="Public Repos">
          {searchedRepos.map((repo) => (
            <AutocompleteItem
              data-testid="github-repo-item"
              key={repo.id}
              value={repo.id}
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
      )}
    </Autocomplete>
  );
}
