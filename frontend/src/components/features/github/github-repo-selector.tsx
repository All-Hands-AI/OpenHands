import React from "react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { useDebounce } from "#/hooks/use-debounce";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";

interface GitHubRepositorySelectorProps {
  onSelect: () => void;
  repositories: GitHubRepository[];
}

function sanitizeQuery(query: string) {
  let sanitizedQuery = query.replace(/https?:\/\//, "");
  sanitizedQuery = sanitizedQuery.replace(/github.com\//, "");
  sanitizedQuery = sanitizedQuery.replace(/\.git$/, "");
  sanitizedQuery = sanitizedQuery.toLowerCase();
  return sanitizedQuery;
}

export function GitHubRepositorySelector({
  onSelect,
  repositories,
}: GitHubRepositorySelectorProps) {
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const { data: searchedRepos = [] } = useSearchRepositories(
    sanitizeQuery(debouncedSearchQuery),
  );

  const finalRepositories: GitHubRepository[] = [
    ...(config?.APP_MODE === "saas" && config?.APP_SLUG
      ? [
          {
            id: -1000,
            full_name: "Add more repositories...",
          } as GitHubRepository,
        ]
      : []),
    ...searchedRepos.filter(
      (repo) => !repositories.find((r) => r.id === repo.id),
    ),
    ...repositories.filter(
      (repo) =>
        !debouncedSearchQuery ||
        sanitizeQuery(repo.full_name).includes(
          sanitizeQuery(debouncedSearchQuery),
        ),
    ),
  ];

  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = finalRepositories.find((r) => r.id.toString() === id);
    if (!repo) return;

    if (repo.id === -1000) {
      window.open(
        `https://github.com/apps/${config?.APP_SLUG}/installations/new`,
        "_blank",
      );
      return;
    }

    dispatch(setSelectedRepository(repo.full_name));
    posthog.capture("repository_selected");
    onSelect();
    setSelectedKey(id);
  };

  const handleClearSelection = () => {
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
      items={finalRepositories}
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
        sanitizeQuery(textValue).includes(sanitizeQuery(inputValue))
      }
    >
      {(item) => {
        const isPublicRepo = !repositories.find((r) => r.id === item.id);
        return (
          <AutocompleteItem
            data-testid="github-repo-item"
            key={item.id}
            value={item.id}
            className="data-[selected=true]:bg-default-100"
            textValue={item.full_name}
          >
            {item.full_name}
            {isPublicRepo && item.stargazers_count !== undefined && (
              <span className="ml-1 text-gray-400">
                ({item.stargazers_count}⭐)
              </span>
            )}
          </AutocompleteItem>
        );
      }}
    </Autocomplete>
  );
}
