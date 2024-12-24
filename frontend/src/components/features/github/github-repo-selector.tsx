import React from "react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { openHands } from "#/api/open-hands-axios";

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

  React.useEffect(() => {
    const searchPublicRepo = async () => {
      if (searchQuery.trim()) {
        try {
          const response = await openHands.get<{ items: GitHubRepository[] }>("/api/github/search/repositories", {
            params: {
              q: searchQuery,
              per_page: 1,
              sort: "updated",
              order: "desc"
            }
          });
          if (response.data.items.length > 0) {
            setSearchedRepo(response.data.items[0]);
          } else {
            setSearchedRepo(null);
          }
        } catch (error) {
          console.error("Error searching repositories:", error);
          setSearchedRepo(null);
        }
      } else {
        setSearchedRepo(null);
      }
    };

    const debounceTimeout = setTimeout(searchPublicRepo, 300);
    return () => clearTimeout(debounceTimeout);
  }, [searchQuery]);

  // Add option to install app onto more repos and include searched repo if found
  const finalRepositories = [
    ...(config?.APP_MODE === "saas" ? [{ id: -1000, full_name: "Add more repositories..." }] : []),
    ...(searchedRepo ? [{
      ...searchedRepo,
      full_name: `${searchedRepo.full_name} (${searchedRepo.stargazers_count}⭐)`
    }] : []),
    ...repositories
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
