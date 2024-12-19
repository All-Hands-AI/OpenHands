import React from "react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { useState } from "react";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useRepositorySearch } from "#/hooks/query/use-repository-search";
import { useConfig } from "#/hooks/query/use-config";

interface GitHubRepositorySelectorProps {
  onSelect: () => void;
}

export function GitHubRepositorySelector({
  onSelect,
}: GitHubRepositorySelectorProps) {
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);

  // Add option to install app onto more repos
  const finalRepositories =
    config?.APP_MODE === "saas"
      ? [{ id: -1000, full_name: "Add more repositories..." }, ...repositories]
      : repositories;

  const dispatch = useDispatch();
  const [searchQuery, setSearchQuery] = useState("");
  const { repositories, isLoading } = useRepositorySearch(searchQuery);

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
      placeholder="Type a repository name or select from your repositories"
      selectedKey={selectedKey}
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
      }}
      onInputChange={(value) => setSearchQuery(value)}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      clearButtonProps={{ onClick: handleClearSelection }}
      isLoading={isLoading}
      listboxProps={{
        emptyContent,
      }}
    >
      {finalRepositories.map((repo) => (
        <AutocompleteItem
          data-testid="github-repo-item"
          key={repo.id}
          value={repo.id}
          className="flex items-center justify-between"
        >
          <span>{repo.full_name}</span>
          {repo.stargazers_count > 0 && (
            <span className="text-xs text-neutral-400">
              ⭐ {repo.stargazers_count.toLocaleString()}
            </span>
          )}
        </AutocompleteItem>
      ))}
    </Autocomplete>
  );
}
